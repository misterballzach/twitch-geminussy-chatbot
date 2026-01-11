import os, sys, json, ssl, socket, asyncio, random, threading, requests, time, textwrap, traceback
import websocket
from database import create_tables, create_or_update_user, get_user, get_random_active_user, update_user_facts
from ai_client import generate_ai_response, perform_google_search, extract_user_facts
from games import GameManager
import hashlib

# ---------------- HELPERS ----------------
def validate_token(token):
    try:
        url = "https://id.twitch.tv/oauth2/validate"
        headers = {"Authorization": f"OAuth {token.replace('oauth:', '')}"}
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        client_id = data.get("client_id")
        user_id = data.get("user_id")
        scopes = data.get("scopes", [])

        if "channel:read:ads" not in scopes:
            print("[WARNING] Token missing 'channel:read:ads' scope. Auto-ad detection will not work.")

        return client_id, user_id, scopes
    except Exception as e:
        print(f"[ERROR] Token validation failed: {e}")
        return None, None, []

def get_broadcaster_id(username, client_id, token):
    try:
        url = f"https://api.twitch.tv/helix/users?login={username}"
        headers = {
            "Client-ID": client_id,
            "Authorization": f"Bearer {token.replace('oauth:', '')}"
        }
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data["data"]:
            return data["data"][0]["id"]
    except Exception as e:
        print(f"[ERROR] Failed to resolve broadcaster ID for {username}: {e}")
    return None

# ---------------- CONFIG ----------------
CONFIG_FILE = "bot_config.json"
MEMORY = {"chat_history": []}

def prompt_missing_config(config):
    required = ["bot_username", "bot_token", "gemini_api_key", "personality", "auto_chat_freq"]
    optional = ["google_search_api_key", "google_search_engine_id", "caption_file_path"]
    updated = False

    for field in required:
        if field not in config or config[field] in [None, ""]:
            if field == "personality":
                val = input("Enter bot personality (default: Friendly, humorous, chatty): ").strip() or "Friendly, humorous, chatty"
            elif field == "auto_chat_freq":
                while True:
                    try:
                        val = float(input("Enter auto-chat frequency (0-1, default 0.2): ").strip() or 0.2)
                        if 0 <= val <= 1: break
                    except: continue
            else:
                val = input(f"Enter {field.replace('_',' ')}: ").strip()
                if field == "gemini_api_key":
                    val = val.strip('\'" ,')
            config[field] = val
            updated = True

    for field in optional:
        if field not in config:
            val = input(f"Enter {field.replace('_',' ')} (optional, press Enter to skip): ").strip()
            if val:
                if field == "caption_file_path":
                    # Remove quotes if user added them
                    val = val.strip('\'"')
                else:
                    # Strip quotes and extra spaces for keys/ids
                    val = val.strip('\'" ')
                config[field] = val
                updated = True
            else:
                config[field] = ""
                updated = True

    if updated:
        with open(CONFIG_FILE, "w") as f: json.dump(config, f, indent=4)
    return config

def load_or_create_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f: config = json.load(f)

        # Sanitize keys
        for key in ["google_search_api_key", "google_search_engine_id", "gemini_api_key"]:
            if key in config and isinstance(config[key], str):
                config[key] = config[key].strip('\'" \n')

        # Check for username as API key
        if "google_search_api_key" in config and "bot_username" in config:
            if config["google_search_api_key"] == config["bot_username"]:
                print(f"[WARNING] Your Google Search API Key is set to '{config['google_search_api_key']}', which matches your bot username. This is likely incorrect.")

        if sys.stdin.isatty():
            config = prompt_missing_config(config)
    else:
        if sys.stdin.isatty():
            config = prompt_missing_config({})
        else:
            print("ERROR: bot_config.json not found. Please run interactively once to create it.")
            sys.exit(1)

    if "socials" not in config:
        config["socials"] = {}

    if "moderation" not in config:
        config["moderation"] = {
            "banned_words": [],
            "link_filtering": True,
            "caps_filtering": True,
            "timeout_duration": 60
        }

    if "sentiment_analysis_probability" not in config:
        config["sentiment_analysis_probability"] = 0.1

    if "auto_chat_interval" not in config:
        config["auto_chat_interval"] = 600

    if "personality_traits" not in config:
        config["personality_traits"] = {
            "likes": [],
            "dislikes": []
        }

    if "delay_settings" not in config:
        config["delay_settings"] = {
            "base_delay": 1.0,
            "delay_per_character": 0.01
        }

    if "max_response_length" not in config:
        config["max_response_length"] = 450

    if "conversation_starter_interval" not in config:
        config["conversation_starter_interval"] = 900

    if sys.stdin.isatty():
        channels_input = input("Enter Twitch channels (comma separated): ").strip()
        channels = [c.strip().lstrip("#") for c in channels_input.split(",") if c.strip()]
        config["channels"] = channels
        with open(CONFIG_FILE, "w") as f: json.dump(config, f, indent=4)
        print("Config loaded and saved.")

    if "channels" not in config:
        config["channels"] = []

    return config

# ---------------- CONTEXT MONITOR ----------------
class ContextMonitor:
    def __init__(self, file_path, max_lines=20):
        self.file_path = file_path
        self.max_lines = max_lines
        self.context_buffer = []
        self.last_modified = 0
        if file_path:
            threading.Thread(target=self.monitor_file, daemon=True).start()

    def monitor_file(self):
        while True:
            try:
                if os.path.exists(self.file_path):
                    mtime = os.path.getmtime(self.file_path)
                    if mtime > self.last_modified:
                        self.last_modified = mtime
                        with open(self.file_path, "r", encoding="utf-8", errors="ignore") as f:
                            lines = f.readlines()
                            # Just take the last N lines
                            self.context_buffer = [line.strip() for line in lines[-self.max_lines:] if line.strip()]
            except Exception as e:
                print(f"[ERROR] Context monitor failed: {e}")
            time.sleep(1)

    def get_context(self):
        return "\n".join(self.context_buffer)

# ---------------- EVENTSUB CLIENT ----------------
class TwitchEventSub:
    def __init__(self, config, on_ad_break_callback):
        self.config = config
        self.on_ad_break = on_ad_break_callback
        self.ws = None
        self.session_id = None
        self.client_id = None
        self.token = self.config["bot_token"]
        self.broadcaster_ids = {}

    def start(self):
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        # 1. Validate token and get Client ID
        self.client_id, user_id, scopes = validate_token(self.token)
        if not self.client_id:
            print("[EVENTSUB] Failed to get Client ID. EventSub disabled.")
            return

        # 2. Resolve Broadcaster IDs
        for ch in self.config["channels"]:
            bid = get_broadcaster_id(ch, self.client_id, self.token)
            if bid:
                # IMPORTANT: Ad detection requires the token to belong to the broadcaster
                if bid == user_id:
                    self.broadcaster_ids[ch] = bid
                else:
                    print(f"[EVENTSUB] Skipping ad detection for {ch}. Bot token does not belong to the broadcaster.")
            else:
                print(f"[EVENTSUB] Could not find ID for channel {ch}")

        if not self.broadcaster_ids:
            print("[EVENTSUB] No valid channels to monitor (Token must belong to Broadcaster).")
            return

        # 3. Connect to WebSocket
        websocket.enableTrace(False)
        self.ws = websocket.WebSocketApp("wss://eventsub.wss.twitch.tv/ws",
                                         on_open=self._on_open,
                                         on_message=self._on_message,
                                         on_error=self._on_error,
                                         on_close=self._on_close)
        self.ws.run_forever()

    def _on_open(self, ws):
        print("[EVENTSUB] Connected to Twitch EventSub.")

    def _on_message(self, ws, message):
        try:
            data = json.loads(message)
            msg_type = data.get("metadata", {}).get("message_type")

            if msg_type == "session_welcome":
                self.session_id = data.get("payload", {}).get("session", {}).get("id")
                print(f"[EVENTSUB] Session Welcome. ID: {self.session_id}")
                self._subscribe_to_ads()

            elif msg_type == "notification":
                payload = data.get("payload", {})
                subscription = payload.get("subscription", {})
                event = payload.get("event", {})

                if subscription.get("type") == "channel.ad_break.begin":
                    duration = event.get("duration_seconds", 0)
                    broadcaster_id = event.get("broadcaster_user_id")
                    # Find channel name from ID
                    channel = next((name for name, bid in self.broadcaster_ids.items() if bid == broadcaster_id), None)
                    if channel:
                        print(f"[EVENTSUB] Ad break detected on {channel} for {duration}s")
                        self.on_ad_break(channel, duration)

        except Exception as e:
            print(f"[EVENTSUB] Error parsing message: {e}")

    def _subscribe_to_ads(self):
        if not self.session_id: return

        url = "https://api.twitch.tv/helix/eventsub/subscriptions"
        headers = {
            "Client-ID": self.client_id,
            "Authorization": f"Bearer {self.token.replace('oauth:', '')}",
            "Content-Type": "application/json"
        }

        for ch, bid in self.broadcaster_ids.items():
            payload = {
                "type": "channel.ad_break.begin",
                "version": "1",
                "condition": {"broadcaster_user_id": bid},
                "transport": {
                    "method": "websocket",
                    "session_id": self.session_id
                }
            }
            try:
                resp = requests.post(url, headers=headers, json=payload, timeout=10)
                if resp.status_code in [200, 202]:
                    print(f"[EVENTSUB] Subscribed to ads for {ch}")
                elif resp.status_code == 409:
                    print(f"[EVENTSUB] Already subscribed for {ch}")
                else:
                    print(f"[EVENTSUB] Subscription failed for {ch}: {resp.text}")
            except Exception as e:
                print(f"[EVENTSUB] Sub req failed: {e}")

    def _on_error(self, ws, error):
        print(f"[EVENTSUB] Error: {error}")

    def _on_close(self, ws, close_status_code, close_msg):
        print("[EVENTSUB] Disconnected. Reconnecting in 10s...")
        time.sleep(10)
        self.start() # Simple reconnect

# ---------------- SEARCH & AI & FACTS (Moved to ai_client.py) ----------------

def analyze_sentiment_and_update_preferences(message, user, config):
    prompt = f"Analyze the sentiment of the following message and identify the main topics. Respond with a JSON object with two keys: 'sentiment' (either 'positive', 'negative', or 'neutral') and 'topics' (a list of strings). Message: {message}"

    response_text = generate_ai_response(prompt, user, config)

    # Clean up markdown if present
    if response_text.startswith("```json"):
        response_text = response_text[7:]
    if response_text.startswith("```"):
        response_text = response_text[3:]
    if response_text.endswith("```"):
        response_text = response_text[:-3]
    response_text = response_text.strip()

    try:
        response_json = json.loads(response_text)

        sentiment = response_json.get("sentiment")
        topics = response_json.get("topics", [])

        if sentiment == "positive":
            config["personality_traits"]["likes"].extend(topics)
            create_or_update_user(user, favouritism_score_increment=1)
        elif sentiment == "negative":
            config["personality_traits"]["dislikes"].extend(topics)
            create_or_update_user(user, favouritism_score_increment=-1)

        # Remove duplicates
        config["personality_traits"]["likes"] = list(set(config["personality_traits"]["likes"]))
        config["personality_traits"]["dislikes"] = list(set(config["personality_traits"]["dislikes"]))

        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)

    except Exception as e:
        print(f"[ERROR] Sentiment analysis failed: {e}")
        print(f"[DEBUG] Failed text: {response_text}")

# ---------------- MEMORY ----------------
def save_memory(user, msg, response):
    MEMORY["chat_history"].append({"user": user, "message": msg, "response": response})
    if len(MEMORY["chat_history"]) > 50:
        MEMORY["chat_history"] = MEMORY["chat_history"][-50:]

def get_recent_memory(n=5):
    return MEMORY["chat_history"][-n:]

# ---------------- IRC BOT ----------------
class IRCBot:
    def __init__(self, config):
        self.server = "irc.chat.twitch.tv"
        self.port = 6667
        self.config = config
        self.nick = self.config["bot_username"]
        self.token = self.config["bot_token"]
        self.channels = self.config["channels"]
        self.sock = None
        self.loop = asyncio.get_event_loop()
        self.sock_lock = threading.Lock()
        self.commands = {
            "ai": self.ai_command,
            "gemini": self.gemini_command,
            "say": self.say_command,
            "uptime": self.uptime_command,
            "socials": self.socials_command,
            "commands": self.commands_command,
            "trivia": self.trivia_command,
            "guess": self.guess_command,
            "scramble": self.scramble_command,
            "rps": self.rps_command,
            "roast": self.roast_command,
            "8ball": self.eightball_command,
            "love": self.love_command,
            "brb": self.brb_command,
            "back": self.back_command,
            "lurk": self.lurk_command,
            "raidmsg": self.raidmsg_command,
            "raidout": self.raidout_command
        }
        self.context_monitor = ContextMonitor(self.config.get("caption_file_path"))
        self.game_manager = GameManager(self.config, self.send_message)
        self.is_brb = False
        self.is_ad_break = False
        self.original_auto_chat_freq = self.config.get("auto_chat_freq", 0.2)
        self.brb_timer = None

        # Expose bot instance globally for the generate_ai_response function to access context monitor
        global bot_instance
        bot_instance = self

        create_tables()

        # Start EventSub
        self.eventsub = TwitchEventSub(self.config, self.start_ad_mode)
        self.eventsub.start()

        threading.Thread(target=self.connect_and_listen, daemon=True).start()
        self.auto_chat_timer = threading.Timer(self.config.get("auto_chat_interval", 600), self.auto_chat)
        self.auto_chat_timer.start()
        self.conversation_starter_timer = threading.Timer(self.config.get("conversation_starter_interval", 900), self.conversation_starter_task)
        self.conversation_starter_timer.start()

    def connect_and_listen(self):
        while True:
            try:
                print(f"[IRC] Connecting to {self.server}:{self.port} as {self.nick}")
                self.sock = socket.socket()
                self.sock.connect((self.server, self.port))
                self.sock.send(f"PASS {self.token}\r\n".encode("utf-8"))
                self.sock.send(f"NICK {self.nick}\r\n".encode("utf-8"))
                for ch in self.channels:
                    self.sock.send(f"JOIN #{ch}\r\n".encode("utf-8"))
                print(f"[IRC] Connected and joined channels: {', '.join(self.channels)}")
                self.listen()
            except Exception as e:
                print(f"[ERROR] IRC connect failed: {e}")
                if self.sock: self.sock.close()
                time.sleep(5)

    def listen(self):
        buffer = ""
        while True:
            try:
                data = self.sock.recv(1024).decode("utf-8", errors="ignore")
                if not data: raise Exception("Disconnected")
                buffer += data
                while "\r\n" in buffer:
                    line, buffer = buffer.split("\r\n", 1)
                    self.handle_line(line)
            except Exception as e:
                print(f"[ERROR] IRC recv error: {e}")
                if self.sock: self.sock.close()
                break

    def handle_line(self, line):
        try:
            print(f"[IRC RAW] {line}")
            if line.startswith("PING"):
                self.sock.send(f"PONG {line.split()[1]}\r\n".encode("utf-8"))
            elif "PRIVMSG" in line:
                parts = line.split(":", 2)
                if len(parts) < 3: return
                user = parts[1].split("!")[0]
                channel = parts[1].split(" ")[2][1:]
                message = parts[2]
                print(f"[CHAT] {user}: {message}")

                create_or_update_user(user, message_count_increment=1)

                if random.random() < self.config.get("sentiment_analysis_probability", 0.1):
                    analyze_sentiment_and_update_preferences(message, user, self.config)

                if self.moderate_message(message, user, channel):
                    return

                if message.startswith("!"):
                    command_parts = message.split(" ", 1)
                    command = command_parts[0][1:].lower()
                    args = command_parts[1] if len(command_parts) > 1 else ""
                    self.handle_command(command, args, user, channel)
                else:
                    # Check for active game answers
                    response, points = self.game_manager.handle_message(channel, user, message)
                    if response:
                        self.send_message(response, channel)
                        if points > 0:
                            create_or_update_user(user, favouritism_score_increment=points)

                    if self.nick.lower() in message.lower():
                        # Try to extract facts from the message
                        threading.Thread(target=extract_user_facts, args=(message, user, self.config)).start()

                        prompt = message
                        context = "\n".join([f"{m['user']}: {m['message']}\nBot: {m['response']}" for m in get_recent_memory()])
                    resp = generate_ai_response(f"{context}\n{user} says: {prompt}", user, self.config, context_monitor=self.context_monitor)
                    save_memory(user, prompt, resp)
                    self.send_message(resp, channel)

            elif "USERNOTICE" in line:
                parts = line.split(":", 2)
                if len(parts) < 3: return
                message = parts[2]
                tags = {t.split("=")[0]: t.split("=")[1] for t in parts[0].split(";") if "=" in t}
                # Usernotice channel (not fully parsed above but usually after USERNOTICE)
                # Format: ... USERNOTICE #channel ...
                channel = parts[1].split(" ")[2][1:]

                if tags.get("msg-id") == "sub" or tags.get("msg-id") == "resub":
                    user = tags.get("display-name")
                    if user:
                        create_or_update_user(user, is_subscriber=True, favouritism_score_increment=10)
                        # AI Subscription Welcome
                        def _sub_welcome_task():
                            prompt = f"User '{user}' just subscribed! Thank them enthusiastically in your personality."
                            response = generate_ai_response(prompt, user, self.config, context_monitor=self.context_monitor)
                            self.send_message(response, channel)
                        threading.Thread(target=_sub_welcome_task).start()

                elif tags.get("msg-id") == "raid":
                    user = tags.get("display-name")
                    viewers = tags.get("msg-param-viewerCount")
                    if user and viewers:
                        # AI Raid Welcome
                        def _raid_welcome_task():
                            prompt = f"User '{user}' just raided with {viewers} viewers! Give them a warm, hype welcome in your personality."
                            response = generate_ai_response(prompt, user, self.config, context_monitor=self.context_monitor)
                            self.send_message(response, channel)
                        threading.Thread(target=_raid_welcome_task).start()
        except Exception as e:
            print(f"[ERROR] Error in handle_line: {e}")
            traceback.print_exc()

    def handle_command(self, command, args, user, channel):
        if command in self.commands:
            self.commands[command](args, user, channel)

    def ai_command(self, args, user, channel):
        prompt = args
        context = "\n".join([f"{m['user']}: {m['message']}\nBot: {m['response']}" for m in get_recent_memory()])
        resp = generate_ai_response(f"{context}\n{user} says: {prompt}", user, self.config, context_monitor=self.context_monitor)
        save_memory(user, prompt, resp)
        self.send_message(resp, channel)

    def gemini_command(self, args, user, channel):
        query = args
        if not query:
            self.send_message("Please provide a query for Gemini.", channel)
            return

        api_key = self.config.get("google_search_api_key")
        engine_id = self.config.get("google_search_engine_id")

        if not api_key or not engine_id:
            self.send_message("Google Search is not configured.", channel)
            return

        self.send_message(f"Searching for '{query}'...", channel)
        search_results = perform_google_search(query, api_key, engine_id)

        if search_results.startswith("Search failed:"):
            self.send_message(f"Search failed. Please check your Google Search API key and Engine ID. Error: {search_results.replace('Search failed: ', '')}", channel)
            return

        prompt = f"The user '{user}' asked: '{query}'.\n\nHere is some background information:\n{search_results}\n\nUsing this information, answer the user's question. Respond as a natural, organic participant in the chat. Do NOT mention that you performed a search or say 'according to the results'. Just give the answer or opinion as if you knew it. You can share relevant links naturally (e.g., 'I found this link:', 'Check this out:') if they add value."

        response_text = generate_ai_response(prompt, user, self.config, context_monitor=self.context_monitor)

        # Save to memory so the conversation context is preserved
        save_memory(user, query, response_text)

        self.send_message(f"@{user} {response_text}", channel)

    def say_command(self, args, user, channel):
        self.send_message(args, channel)

    def uptime_command(self, args, user, channel):
        try:
            url = f"https://decapi.me/twitch/uptime/{channel}"
            response = requests.get(url)
            response.raise_for_status()
            self.send_message(f"Stream has been live for: {response.text}", channel)
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Uptime command failed: {e}")
            self.send_message("Could not retrieve uptime.", channel)

    def socials_command(self, args, user, channel):
        if "socials" in self.config and self.config["socials"]:
            socials_message = "Follow us on social media: " + ", ".join([f"{platform}: {link}" for platform, link in self.config["socials"].items()])
            self.send_message(socials_message, channel)
        else:
            self.send_message("No social media links configured.", channel)

    def commands_command(self, args, user, channel):
        commands_list = "!".join(self.commands.keys())
        self.send_message(f"Available commands: !{commands_list}", channel)

    def trivia_command(self, args, user, channel):
        msg = self.game_manager.start_game("trivia", channel, user)
        self.send_message(msg, channel)

    def guess_command(self, args, user, channel):
        msg = self.game_manager.start_game("guess", channel, user)
        self.send_message(msg, channel)

    def scramble_command(self, args, user, channel):
        msg = self.game_manager.start_game("scramble", channel, user)
        self.send_message(msg, channel)

    def rps_command(self, args, user, channel):
        if not args:
            self.send_message(f"@{user}, usage: !rps <rock|paper|scissors>", channel)
            return

        user_choice = args.lower().strip()
        if user_choice not in ["rock", "paper", "scissors"]:
            self.send_message(f"@{user}, please choose rock, paper, or scissors!", channel)
            return

        bot_choice = random.choice(["rock", "paper", "scissors"])
        result = ""

        if user_choice == bot_choice:
            result = "It's a tie!"
        elif (user_choice == "rock" and bot_choice == "scissors") or \
             (user_choice == "paper" and bot_choice == "rock") or \
             (user_choice == "scissors" and bot_choice == "paper"):
            result = "You win! 🎉"
            create_or_update_user(user, favouritism_score_increment=1)
        else:
            result = "I win! 😈"

        self.send_message(f"@{user} chose {user_choice}, I chose {bot_choice}. {result}", channel)

    def roast_command(self, args, user, channel):
        target = args.strip() or user
        prompt = f"Give me a funny, lighthearted roast for the user '{target}'. Keep it friendly and Twitch-safe."
        response = generate_ai_response(prompt, user, self.config, context_monitor=self.context_monitor)
        self.send_message(f"@{target} 🔥 {response}", channel)

    def eightball_command(self, args, user, channel):
        if not args:
            self.send_message(f"@{user}, ask me a question!", channel)
            return

        responses = [
            "It is certain.", "It is decidedly so.", "Without a doubt.", "Yes definitely.", "You may rely on it.",
            "As I see it, yes.", "Most likely.", "Outlook good.", "Yes.", "Signs point to yes.",
            "Reply hazy, try again.", "Ask again later.", "Better not tell you now.", "Cannot predict now.", "Concentrate and ask again.",
            "Don't count on it.", "My reply is no.", "My sources say no.", "Outlook not so good.", "Very doubtful."
        ]
        response = random.choice(responses)
        self.send_message(f"🎱 {response}", channel)

    def love_command(self, args, user, channel):
        target = args.strip()
        if not target:
            self.send_message(f"@{user}, who do you want to check love compatibility with?", channel)
            return

        # Deterministic love calculator based on names
        combined = "".join(sorted([user.lower(), target.lower()]))
        score = int(hashlib.sha256(combined.encode("utf-8")).hexdigest(), 16) % 101

        msg = ""
        if score > 90: msg = "It's destiny! ❤️"
        elif score > 70: msg = "Hot stuff! 🔥"
        elif score > 40: msg = "Maybe just friends? 🤝"
        else: msg = "Oof... 🧊"

        self.send_message(f"❤️ Love User Compatibility: {user} + {target} = {score}%! {msg}", channel)

    def lurk_command(self, args, user, channel):
        def _lurk_task():
            prompt = f"User '{user}' is going into lurk mode (watching silently). Respond with a friendly/funny confirmation in your personality."
            response = generate_ai_response(prompt, user, self.config, context_monitor=self.context_monitor)
            self.send_message(response, channel)
        threading.Thread(target=_lurk_task).start()

    def raidmsg_command(self, args, user, channel):
        def _raidmsg_task():
            prompt = "Write a hype raid message for our community to copy-paste when we raid another stream. It should be short, energetic, and include our channel emotes if you know them, or generic hype emotes."
            response = generate_ai_response(prompt, user, self.config, context_monitor=self.context_monitor)
            self.send_message(response, channel)
        threading.Thread(target=_raidmsg_task).start()

    def raidout_command(self, args, user, channel):
        target_user = args.strip()
        if not target_user:
            self.send_message(f"@{user}, usage: !raidout <target_channel>", channel)
            return

        def _raidout_task():
            # 1. Generate hype message
            prompt = f"We are raiding '{target_user}'. Write a short, spunky, hype raid message for my community to copy-paste. Include emojis. Keep it under 150 chars."
            message = generate_ai_response(prompt, user, self.config, context_monitor=self.context_monitor)

            # 2. Post to local chat
            self.send_message(f"🚨 RAID INCOMING! Copy this: {message}", channel)

            # 3. Trigger Twitch raid via API (more reliable than chat command)
            try:
                client_id, user_id, _ = validate_token(self.token)
                target_id = get_broadcaster_id(target_user, client_id, self.token)

                if user_id and target_id:
                    url = f"https://api.twitch.tv/helix/raids?from_broadcaster_id={user_id}&to_broadcaster_id={target_id}"
                    headers = {
                        "Client-ID": client_id,
                        "Authorization": f"Bearer {self.token.replace('oauth:', '')}"
                    }
                    resp = requests.post(url, headers=headers, timeout=10)
                    if resp.status_code in [200, 201, 204]:
                        print(f"[RAID] Raid initiated via API to {target_user}")
                    else:
                        print(f"[RAID] API Raid failed: {resp.text}. Falling back to chat command.")
                        self.send_message(f"/raid {target_user}", channel)
                else:
                    print("[RAID] Could not resolve IDs. Falling back to chat command.")
                    self.send_message(f"/raid {target_user}", channel)
            except Exception as e:
                print(f"[RAID] API Error: {e}. Falling back to chat command.")
                self.send_message(f"/raid {target_user}", channel)

            # 4. Invasion: Join target channel and post
            try:
                # We need a separate connection or just send JOIN on current socket?
                # Ideally separate to avoid polluting main bot state, but single socket can handle multiple channels.
                # Let's use the main socket but be careful.

                # Check if we are already in the target channel (unlikely for random raids)
                if target_user not in self.channels:
                    with self.sock_lock:
                        self.sock.send(f"JOIN #{target_user}\r\n".encode("utf-8"))
                    time.sleep(2) # Wait for join

                    # Send the hype message
                    with self.sock_lock:
                        self.sock.send(f"PRIVMSG #{target_user} :{message}\r\n".encode("utf-8"))
                    print(f"[RAID] Invaded #{target_user} with: {message}")

                    time.sleep(1)
                    # Leave
                    with self.sock_lock:
                        self.sock.send(f"PART #{target_user}\r\n".encode("utf-8"))
                else:
                    # Already in channel, just send
                    with self.sock_lock:
                        self.sock.send(f"PRIVMSG #{target_user} :{message}\r\n".encode("utf-8"))

            except Exception as e:
                print(f"[ERROR] Raid invasion failed: {e}")

        threading.Thread(target=_raidout_task).start()

    def send_brb_summary(self, channel, user, context_type="brb"):
        try:
            history = get_recent_memory(30)
            history_str = ""
            for entry in history:
                history_str += f"{entry['user']}: {entry['message']}\n"

            if context_type == "ad":
                prompt = f"An ad break has just started. Please summarize the recent conversation (last 20-30 messages) for viewers who might not be subscribed, so they have something to read while the ad plays. Keep it entertaining! Chat History:\n\n{history_str}"
            else:
                prompt = f"The streamer is stepping away (BRB). Please summarize the recent conversation (last 20-30 messages) and spoken context for the chat. Keep it brief and fun. Here is the recent chat history:\n\n{history_str}"

            # generate_ai_response will handle appending the spoken context from context_monitor
            response = generate_ai_response(prompt, user, self.config, context_monitor=self.context_monitor)

            # Check if still in correct mode before sending
            if (context_type == "brb" and self.is_brb) or (context_type == "ad" and self.is_ad_break):
                self.send_message(response)
        except Exception as e:
            print(f"[ERROR] Failed to generate summary: {e}")
        finally:
            # Trigger appropriate game loop
            if context_type == "brb" and self.is_brb:
                self.brb_game_loop(channel)
            elif context_type == "ad" and self.is_ad_break:
                self.ad_game_loop(channel)

    def start_ad_mode(self, channel, duration):
        if self.is_ad_break: return # Already running
        self.is_ad_break = True
        print(f"[BOT] Starting Ad Mode for {duration}s on {channel}")

        self.send_message(f"📺 Ad break started! For those stuck in ads, here's a quick summary of what's happening and a game! (Sub to skip ads!)", channel)

        # Start summary and games
        threading.Thread(target=self.send_brb_summary, args=(channel, "System", "ad")).start()

        # Schedule end of ad mode
        threading.Timer(duration, self.end_ad_mode).start()

    def end_ad_mode(self):
        self.is_ad_break = False
        print("[BOT] Ad Mode ended.")

    def ad_game_loop(self, channel):
        if not self.is_ad_break: return

        msg = self.game_manager.start_random_game(channel)
        if msg:
            self.send_message(msg, channel)

        # Schedule next game quickly (every 60s) during ads if ad is long?
        # Typically ads are 30-180s. One game might be enough.
        # But let's check recursively if ad is still running
        threading.Timer(60, self.ad_game_loop, [channel]).start()

    def brb_command(self, args, user, channel):
        # Check if user is broadcaster or mod?
        # For simplicity, assuming any user can trigger this locally, or ideally restrict to broadcaster
        # In a real bot we'd check badges. For this task, we assume the user running the bot is the owner.
        if self.is_brb:
            self.send_message("I'm already in BRB mode!", channel)
            return

        self.is_brb = True
        self.original_auto_chat_freq = self.config.get("auto_chat_freq", 0.2)
        # Increase engagement
        self.config["auto_chat_freq"] = 0.8

        self.send_message("Streamer is stepping away! 🏃‍♂️💨 Entertainment protocols engaged! Expect games and chaos!", channel)

        # Send summary in background, which will then trigger the game loop
        threading.Thread(target=self.send_brb_summary, args=(channel, user)).start()

    def back_command(self, args, user, channel):
        if not self.is_brb:
            self.send_message("I wasn't in BRB mode, but welcome back!", channel)
            return

        self.is_brb = False
        self.config["auto_chat_freq"] = self.original_auto_chat_freq

        if self.brb_timer:
            self.brb_timer.cancel()

        self.send_message("Streamer is back! 👋 Protocols normalizing.", channel)

    def brb_game_loop(self, channel):
        if not self.is_brb: return

        # Start a random game
        msg = self.game_manager.start_random_game(channel)
        if msg:
            self.send_message(msg)

        # Schedule next game in 2-4 minutes
        interval = random.randint(120, 240)
        self.brb_timer = threading.Timer(interval, self.brb_game_loop, [channel])
        self.brb_timer.start()

    def conversation_starter_task(self):
        user_to_start_conversation_with = get_random_active_user()
        if user_to_start_conversation_with:
            username = user_to_start_conversation_with["username"]
            prompt = f"You want to start a conversation with the user '{username}'. Their favouritism score is {user_to_start_conversation_with['favouritism_score']}. Based on this, what would be a good way to start a conversation with them? Keep it short and natural."
            response = generate_ai_response(prompt, username, self.config, context_monitor=self.context_monitor)
            self.send_message(f"@{username}, {response}")

        self.conversation_starter_timer = threading.Timer(self.config.get("conversation_starter_interval", 900), self.conversation_starter_task)
        self.conversation_starter_timer.start()

    def auto_chat(self):
        if random.random() < self.config.get("auto_chat_freq", 0.2):
            chat_history = get_recent_memory(10)
            if len(chat_history) > 5:
                prompt = "Based on the following chat history, what would be a good comment or question to add to the conversation? Respond in 1 or 2 short sentences. Keep it short and engaging.\n\n"
                for entry in chat_history:
                    prompt += f"{entry['user']}: {entry['message']}\n"

                response = generate_ai_response(prompt, self.nick, self.config, context_monitor=self.context_monitor)
                if len(response) > 200:
                    response = response[:200] + "..."
                self.send_message(response)

        self.auto_chat_timer = threading.Timer(self.config.get("auto_chat_interval", 600), self.auto_chat)
        self.auto_chat_timer.start()

    def moderate_message(self, message, user, channel):
        moderation_config = self.config.get("moderation", {})

        # Banned words
        if moderation_config.get("banned_words"):
            for word in moderation_config["banned_words"]:
                if word in message.lower():
                    self.delete_message(user, channel)
                    self.timeout_user(user, channel)
                    return True

        # Link filtering
        if moderation_config.get("link_filtering"):
            if "http://" in message or "https://" in message or "www." in message:
                self.delete_message(user, channel)
                self.timeout_user(user, channel)
                return True

        # Caps filtering
        if moderation_config.get("caps_filtering"):
            if len(message) > 10 and message.isupper():
                self.delete_message(user, channel)
                self.timeout_user(user, channel)
                return True

        return False

    def delete_message(self, user, channel):
        self.send_message(f"/delete {user}")

    def timeout_user(self, user, channel):
        duration = self.config.get("moderation", {}).get("timeout_duration", 60)
        self.send_message(f"/timeout {user} {duration}")
        create_or_update_user(user, favouritism_score_increment=-5)

    def send_message(self, msg, channel=None):
        if not msg:
            return

        delay_settings = self.config.get("delay_settings", {"base_delay": 1.0, "delay_per_character": 0.01})
        base_delay = delay_settings.get("base_delay", 1.0)
        delay_per_character = delay_settings.get("delay_per_character", 0.01)

        # Split by paragraphs first for natural pauses
        paragraphs = msg.split("\n")
        for paragraph in paragraphs:
            # Split into 500-character chunks
            chunks = textwrap.wrap(paragraph, width=500, replace_whitespace=False)

            target_channels = [channel] if channel else self.channels

            for ch in target_channels:
                for chunk in chunks:
                    delay = base_delay + (len(chunk) * delay_per_character)
                    threading.Thread(target=self._send_message_chunk, args=(ch, chunk, delay)).start()

    def _send_message_chunk(self, channel, chunk, delay):
        try:
            time.sleep(delay)
            with self.sock_lock:
                self.sock.send(f"PRIVMSG #{channel} :{chunk}\r\n".encode("utf-8"))
            print(f"[BOT] Sent to #{channel}: {chunk}")
        except Exception as e:
            print(f"[ERROR] Sending message failed: {e}")

    def get_status_snapshot(self):
        return {
            "chat_history": get_recent_memory(50),
            "captions": self.context_monitor.context_buffer if self.context_monitor else []
        }
