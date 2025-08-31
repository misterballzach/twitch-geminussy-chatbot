"""
Gemini Twitch Bot (IRC version, Python 3.13+)
"""

import os, sys, subprocess, json, random, threading, socket, asyncio, ssl, time, requests
from flask import Flask, render_template_string
from flask_socketio import SocketIO, emit

# ---------------- Install dependencies ----------------
packages = ["flask","flask-socketio","requests","eventlet"]
for pkg in packages:
    try: __import__(pkg)
    except ImportError:
        print(f"Installing {pkg}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

CONFIG_FILE="bot_config.json"
MEMORY={"chat_history":[]}

# ---------------- Config ----------------
def prompt_missing_config(config):
    required = ["bot_username","bot_token","gemini_api_key","personality","auto_chat_freq"]
    updated = False
    for field in required:
        if field not in config or config[field] in [None,""]:
            if field=="personality":
                val = input("Enter bot personality (default: Friendly, humorous, sarcastic, chatty but never annoying): ").strip() or "Friendly, humorous, sarcastic, chatty but never annoying"
            elif field=="auto_chat_freq":
                while True:
                    try: val = float(input("Enter auto-chat frequency (0-1, default 0.2): ").strip() or 0.2)
                    except: continue
                    if 0<=val<=1: break
            else:
                val = input(f"Enter {field.replace('_',' ')}: ").strip()
            config[field]=val
            updated=True
    if updated:
        with open(CONFIG_FILE,"w") as f: json.dump(config,f,indent=4)
    return config

def load_or_create_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE,"r") as f: config=json.load(f)
        config=prompt_missing_config(config)
    else: config=prompt_missing_config({})
    
    channels_input = input("Enter Twitch channels (comma separated): ").strip()
    channels = [c.strip() for c in channels_input.split(",") if c.strip()]
    config["channels"] = channels
    with open(CONFIG_FILE,"w") as f: json.dump(config,f,indent=4)
    print("Config loaded and saved.")
    return config

CONFIG = load_or_create_config()

# ---------------- Gemini AI ----------------
def generate_ai_response(prompt: str) -> str:
    headers = {"X-goog-api-key": CONFIG["gemini_api_key"], "Content-Type":"application/json"}
    data = {
        "contents":[{"parts":[{"text":prompt}]}]
    }
    try:
        resp = requests.post(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
            headers=headers,
            json=data,
            timeout=15
        )
        resp.raise_for_status()
        rj = resp.json()
        try:
            return rj["candidates"][0]["content"]["parts"][0]["text"].strip()
        except KeyError:
            print(f"[ERROR] Unexpected Gemini API response: {rj}")
            return "Hmm… I couldn't come up with a response!"
    except Exception as e:
        print(f"[ERROR] Gemini API call failed: {e}")
        return "Hmm… I couldn't come up with a response!"

# ---------------- Memory ----------------
def save_memory(user, msg, response):
    MEMORY["chat_history"].append({"user":user,"message":msg,"response":response})
    if len(MEMORY["chat_history"])>50: MEMORY["chat_history"]=MEMORY["chat_history"][-50:]
def get_recent_memory(n=5):
    return MEMORY["chat_history"][-n:]

# ---------------- Dashboard ----------------
app = Flask(__name__)
app.config['SECRET_KEY']='secret!'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

DASHBOARD_HTML="""
<!DOCTYPE html>
<html>
<head>
<title>Twitch Bot Dashboard</title>
<script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
</head>
<body>
<h1>Gemini Twitch Bot Dashboard</h1>
<label>Personality:</label>
<input type="text" id="personality" value="{{ personality }}"><br><br>
<label>Auto Chat Frequency:</label>
<input type="range" id="freq" min="0" max="1" step="0.01" value="{{ auto_chat_freq }}">
<span id="freq_val">{{ auto_chat_freq }}</span><br><br>
<label>Send !say Message:</label>
<input type="text" id="say_msg"><button onclick="sendMessage()">Send</button>
<script>
const socket=io();
const personalityInput=document.getElementById("personality");
const freqInput=document.getElementById("freq");
const freqVal=document.getElementById("freq_val");
freqInput.addEventListener("input",()=>{freqVal.innerText=freqInput.value;updateConfig();});
personalityInput.addEventListener("change",updateConfig);
function updateConfig(){socket.emit("update_config",{personality:personalityInput.value,auto_chat_freq:parseFloat(freqInput.value)});}
function sendMessage(){const msg=document.getElementById("say_msg").value;if(msg){socket.emit("send_message",{message:msg});document.getElementById("say_msg").value="";}}
socket.on("config_updated",config=>{personalityInput.value=config.personality;freqInput.value=config.auto_chat_freq;freqVal.innerText=config.auto_chat_freq;});
</script>
</body>
</html>
"""

@app.route("/")
def index(): return DASHBOARD_HTML.replace("{{ personality }}", CONFIG["personality"]).replace("{{ auto_chat_freq }}", str(CONFIG["auto_chat_freq"]))

@socketio.on("update_config")
def handle_update(data):
    CONFIG["personality"] = data.get("personality", CONFIG["personality"])
    CONFIG["auto_chat_freq"] = data.get("auto_chat_freq", CONFIG["auto_chat_freq"])
    with open(CONFIG_FILE,"w") as f: json.dump(CONFIG,f,indent=4)
    emit("config_updated", CONFIG, broadcast=True)

@socketio.on("send_message")
def handle_send_message(data):
    msg = data.get("message")
    if msg and bot:
        rewritten = generate_ai_response(f"Rewrite this in my personality: {msg}")
        save_memory("dashboard", msg, rewritten)
        bot.schedule_send(f"PRIVMSG #{bot.channels[0]} :{rewritten}")

def run_dashboard(): socketio.run(app, port=5000)

# ---------------- IRC Bot ----------------
class IRCBot:
    def __init__(self, username, token, channels):
        self.username = username
        self.token = token
        self.channels = channels
        self.loop = asyncio.get_event_loop()
        self.sock = None
        self.connect()

    def connect(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect(("irc.chat.twitch.tv", 6667))
            self.send_raw(f"PASS {self.token}")
            self.send_raw(f"NICK {self.username}")
            for ch in self.channels:
                self.send_raw(f"JOIN #{ch}")
            print(f"[IRC] Connected and joined channels: {','.join(self.channels)}")
        except Exception as e:
            print(f"[ERROR] IRC connect failed: {e}")
            time.sleep(5)
            self.connect()

    def send_raw(self, msg):
        try:
            self.sock.send((msg + "\r\n").encode())
        except Exception as e:
            print(f"[ERROR] IRC send failed: {e}")

    def send_message(self, msg):
        for ch in self.channels:
            self.send_raw(f"PRIVMSG #{ch} :{msg}")
            print(f"[IRC SEND] #{ch}: {msg}")

    def schedule_send(self, msg):
        asyncio.run_coroutine_threadsafe(self._async_send(msg), self.loop)

    async def _async_send(self, msg):
        self.send_message(msg)

    def recv_loop(self):
        buffer = ""
        while True:
            try:
                data = self.sock.recv(4096).decode()
                if not data:
                    raise Exception("No data received")
                buffer += data
                while "\r\n" in buffer:
                    line, buffer = buffer.split("\r\n", 1)
                    self.handle_line(line)
            except Exception as e:
                print(f"[IRC] Reconnecting due to error: {e}")
                time.sleep(5)
                self.connect()
                buffer = ""

    def handle_line(self, line):
        print(f"[IRC RAW] {line}")
        if line.startswith("PING"):
            self.send_raw(f"PONG {line.split()[1]}")
        elif "PRIVMSG" in line:
            parts = line.split(":", 2)
            if len(parts) < 3: return
            prefix, channel, msg = parts
            user = prefix.split("!")[0][1:]
            self.handle_message(user, channel.strip(), msg.strip())

    def handle_message(self, user, channel, content):
        print(f"[CHAT] {user}@{channel}: {content}")
        if content.startswith("!ai "):
            user_msg = content[4:]
            recent = get_recent_memory()
            context = "\n".join([f"{m['user']}: {m['message']}\nBot: {m['response']}" for m in recent])
            prompt = f"{context}\n{user} says: {user_msg}"
            response = generate_ai_response(prompt)
            save_memory(user,user_msg,response)
            self.send_message(response)
        elif content.startswith("!say "):
            user_msg = content[5:]
            response = generate_ai_response(f"Rewrite this in my personality: {user_msg}")
            save_memory(user,user_msg,response)
            self.send_message(response)

# ---------------- Auto Chat ----------------
def auto_chat_loop():
    while True:
        time.sleep(30)
        if random.random() < CONFIG["auto_chat_freq"]:
            prompt = random.choice(["Say something funny","Ask viewers a question","Share a quirky fact"])
            response = generate_ai_response(prompt)
            if bot: bot.schedule_send(response)

# ---------------- Run ----------------
if __name__=="__main__":
    bot = IRCBot(CONFIG["bot_username"], CONFIG["bot_token"], CONFIG["channels"])
    threading.Thread(target=bot.recv_loop, daemon=True).start()
    threading.Thread(target=auto_chat_loop, daemon=True).start()
    threading.Thread(target=run_dashboard, daemon=True).start()
    while True: time.sleep(1)
