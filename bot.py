import os, sys, json, ssl, socket, asyncio, random, threading, requests, time, textwrap
from database import create_tables, create_or_update_user, get_user

# ---------------- CONFIG ----------------
CONFIG_FILE = "bot_config.json"
MEMORY = {"chat_history": []}

def prompt_missing_config(config):
    required = ["bot_username", "bot_token", "gemini_api_key", "personality", "auto_chat_freq"]
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
    if updated:
        with open(CONFIG_FILE, "w") as f: json.dump(config, f, indent=4)
    return config

def load_or_create_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f: config = json.load(f)
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

    if sys.stdin.isatty():
        channels_input = input("Enter Twitch channels (comma separated): ").strip()
        channels = [c.strip().lstrip("#") for c in channels_input.split(",") if c.strip()]
        config["channels"] = channels
        with open(CONFIG_FILE, "w") as f: json.dump(config, f, indent=4)
        print("Config loaded and saved.")

    if "channels" not in config:
        config["channels"] = []

    return config

# ---------------- GEMINI AI ----------------
def generate_ai_response(prompt: str, user, config) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={config['gemini_api_key']}"
    headers = {
        "Content-Type": "application/json",
    }

    user_data = get_user(user)
    favouritism_score = user_data["favouritism_score"] if user_data else 0

    personality_prompt = f"Respond in personality: {config['personality']}"
    if "personality_traits" in config:
        likes = ", ".join(config["personality_traits"].get("likes", []))
        if likes:
            personality_prompt += f"\nLikes: {likes}"
        dislikes = ", ".join(config["personality_traits"].get("dislikes", []))
        if dislikes:
            personality_prompt += f"\nDislikes: {dislikes}"

    prompt_with_context = f"{personality_prompt}\nUser '{user}' has a favouritism score of {favouritism_score}.\n{prompt}"
    data = {"contents":[{"parts":[{"text": prompt_with_context}]}]}

    try:
        r = requests.post(url, headers=headers, json=data, timeout=10)
        r.raise_for_status()
        resp = r.json()

        # Parse Gemini Flash response
        text_parts = []
        candidates = resp.get("candidates", [])
        if candidates:
            content = candidates[0].get("content", {})
            parts = content.get("parts", [])
            for part in parts:
                if "text" in part:
                    text_parts.append(part["text"])
        text = " ".join(text_parts).strip()
        if not text:
            print("[ERROR] Gemini response empty, full JSON:", resp)
            return "Hmm… I couldn't come up with a response!"
        return text
    except Exception as e:
        print(f"[ERROR] Gemini API call failed: {e}, full response: {r.text if 'r' in locals() else 'no response'}")
        return "Hmm… I couldn't come up with a response!"

def analyze_sentiment_and_update_preferences(message, user, config):
    prompt = f"Analyze the sentiment of the following message and identify the main topics. Respond with a JSON object with two keys: 'sentiment' (either 'positive', 'negative', or 'neutral') and 'topics' (a list of strings). Message: {message}"

    response_text = generate_ai_response(prompt, user, config)

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
        self.commands = {
            "ai": self.ai_command,
            "say": self.say_command,
            "uptime": self.uptime_command,
            "socials": self.socials_command,
            "commands": self.commands_command
        }
        create_tables()
        threading.Thread(target=self.connect_and_listen, daemon=True).start()
        self.auto_chat_timer = threading.Timer(self.config.get("auto_chat_interval", 600), self.auto_chat)
        self.auto_chat_timer.start()

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
                elif self.nick.lower() in message.lower():
                    prompt = message
                    context = "\n".join([f"{m['user']}: {m['message']}\nBot: {m['response']}" for m in get_recent_memory()])
                    resp = generate_ai_response(f"{context}\n{user} says: {prompt}", user, self.config)
                    save_memory(user, prompt, resp)
                    self.send_message(resp)

            elif "USERNOTICE" in line:
                parts = line.split(":", 2)
                if len(parts) < 3: return
                message = parts[2]
                tags = {t.split("=")[0]: t.split("=")[1] for t in parts[0].split(";") if "=" in t}

                if tags.get("msg-id") == "sub" or tags.get("msg-id") == "resub":
                    user = tags.get("display-name")
                    if user:
                        create_or_update_user(user, is_subscriber=True, favouritism_score_increment=10)
                        self.send_message(f"Thanks for the subscription, {user}!")

                elif tags.get("msg-id") == "raid":
                    user = tags.get("display-name")
                    viewers = tags.get("msg-param-viewerCount")
                    if user and viewers:
                        self.send_message(f"Welcome to the channel, {user} and their {viewers} raiders!")
        except Exception as e:
            print(f"[ERROR] Error in handle_line: {e}")

    def handle_command(self, command, args, user, channel):
        if command in self.commands:
            self.commands[command](args, user, channel)

    def ai_command(self, args, user, channel):
        prompt = args
        context = "\n".join([f"{m['user']}: {m['message']}\nBot: {m['response']}" for m in get_recent_memory()])
        resp = generate_ai_response(f"{context}\n{user} says: {prompt}", user, self.config)
        save_memory(user, prompt, resp)
        self.send_message(resp)

    def say_command(self, args, user, channel):
        self.send_message(args)

    def uptime_command(self, args, user, channel):
        try:
            url = f"https://decapi.me/twitch/uptime/{channel}"
            response = requests.get(url)
            response.raise_for_status()
            self.send_message(f"Stream has been live for: {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Uptime command failed: {e}")
            self.send_message("Could not retrieve uptime.")

    def socials_command(self, args, user, channel):
        if "socials" in self.config and self.config["socials"]:
            socials_message = "Follow us on social media: " + ", ".join([f"{platform}: {link}" for platform, link in self.config["socials"].items()])
            self.send_message(socials_message)
        else:
            self.send_message("No social media links configured.")

    def commands_command(self, args, user, channel):
        commands_list = "!".join(self.commands.keys())
        self.send_message(f"Available commands: !{commands_list}")

    def auto_chat(self):
        if random.random() < self.config.get("auto_chat_freq", 0.2):
            chat_history = get_recent_memory(10)
            if len(chat_history) > 5:
                prompt = "Based on the following chat history, what would be a good comment or question to add to the conversation? Keep it short and engaging.\n\n"
                for entry in chat_history:
                    prompt += f"{entry['user']}: {entry['message']}\n"

                response = generate_ai_response(prompt, self.nick, self.config)
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

    def send_message(self, msg):
        if not msg:
            return
        # Split by paragraphs first for natural pauses
        paragraphs = msg.split("\n")
        for paragraph in paragraphs:
            # Split into 500-character chunks
            chunks = textwrap.wrap(paragraph, width=500, replace_whitespace=False)
            for ch in self.channels:
                for chunk in chunks:
                    try:
                        self.sock.send(f"PRIVMSG #{ch} :{chunk}\r\n".encode("utf-8"))
                        print(f"[BOT] Sent to #{ch}: {chunk}")
                        time.sleep(5)  # 5-second delay between chunks
                    except Exception as e:
                        print(f"[ERROR] Sending message failed: {e}")
