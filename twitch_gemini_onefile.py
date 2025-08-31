"""
Gemini Twitch Bot (IRC + Gemini Flash) - Python 3.13+
"""

import os, sys, json, ssl, socket, asyncio, random, threading, requests
from flask import Flask, render_template_string
from flask_socketio import SocketIO, emit

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
            config[field] = val
            updated = True
    if updated:
        with open(CONFIG_FILE, "w") as f: json.dump(config, f, indent=4)
    return config

def load_or_create_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f: config = json.load(f)
        config = prompt_missing_config(config)
    else:
        config = prompt_missing_config({})
    channels_input = input("Enter Twitch channels (comma separated): ").strip()
    channels = [c.strip().lstrip("#") for c in channels_input.split(",") if c.strip()]
    config["channels"] = channels
    with open(CONFIG_FILE, "w") as f: json.dump(config, f, indent=4)
    print("Config loaded and saved.")
    return config

CONFIG = load_or_create_config()

# ---------------- GEMINI AI ----------------
def generate_ai_response(prompt: str) -> str:
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": CONFIG["gemini_api_key"]
    }
    data = {"contents":[{"parts":[{"text": f"Respond in personality: {CONFIG['personality']}\n{prompt}"}]}]}
    
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

# ---------------- MEMORY ----------------
def save_memory(user, msg, response):
    MEMORY["chat_history"].append({"user": user, "message": msg, "response": response})
    if len(MEMORY["chat_history"]) > 50:
        MEMORY["chat_history"] = MEMORY["chat_history"][-50:]

def get_recent_memory(n=5):
    return MEMORY["chat_history"][-n:]

# ---------------- DASHBOARD ----------------
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Gemini Twitch Bot Dashboard</title>
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
def index(): return render_template_string(DASHBOARD_HTML, personality=CONFIG["personality"], auto_chat_freq=CONFIG["auto_chat_freq"])

@socketio.on("update_config")
def handle_update(data):
    CONFIG["personality"] = data.get("personality", CONFIG["personality"])
    CONFIG["auto_chat_freq"] = data.get("auto_chat_freq", CONFIG["auto_chat_freq"])
    with open(CONFIG_FILE, "w") as f: json.dump(CONFIG, f, indent=4)
    emit("config_updated", CONFIG, broadcast=True)

@socketio.on("send_message")
def handle_send_message(data):
    msg = data.get("message")
    if msg and bot:
        rewritten = generate_ai_response(f"Rewrite this in my personality: {msg}")
        bot.send_message(f"!say {rewritten}")

def run_dashboard():
    socketio.run(app, port=5000)

# ---------------- IRC BOT ----------------
class IRCBot:
    def __init__(self):
        self.server = "irc.chat.twitch.tv"
        self.port = 6667
        self.nick = CONFIG["bot_username"]
        self.token = CONFIG["bot_token"]
        self.channels = CONFIG["channels"]
        self.sock = None
        self.loop = asyncio.get_event_loop()
        threading.Thread(target=self.connect_and_listen, daemon=True).start()

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
            if message.lower().startswith("!ai "):
                prompt = message[4:]
                context = "\n".join([f"{m['user']}: {m['message']}\nBot: {m['response']}" for m in get_recent_memory()])
                resp = generate_ai_response(f"{context}\n{user} says: {prompt}")
                save_memory(user, prompt, resp)
                self.send_message(resp)
            elif message.lower().startswith("!say "):
                self.send_message(message[5:])

    def send_message(self, msg):
        for ch in self.channels:
            try:
                self.sock.send(f"PRIVMSG #{ch} :{msg}\r\n".encode("utf-8"))
                print(f"[BOT] Sent to #{ch}: {msg}")
            except Exception as e:
                print(f"[ERROR] Sending message failed: {e}")

# ---------------- RUN ----------------
if __name__ == "__main__":
    bot = IRCBot()
    threading.Thread(target=run_dashboard, daemon=True).start()
    try:
        asyncio.get_event_loop().run_forever()
    except RuntimeError:
        asyncio.new_event_loop().run_forever()
