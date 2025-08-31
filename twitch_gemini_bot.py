import asyncio
import random
import json
import requests
from twitchio.ext import commands, tasks
from threading import Thread
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

# ---------------- CONFIG ----------------
CONFIG_FILE = "bot_config.json"
MEMORY_FILE = "memory.json"

with open(CONFIG_FILE) as f:
    config = json.load(f)

BOT_USERNAME = config["bot_username"]
BOT_TOKEN = config["bot_token"]
CHANNEL = config["channel"]
GEMINI_API_KEY = config["gemini_api_key"]
PERSONALITY = config.get("personality")
AUTO_CHAT_FREQ = config.get("auto_chat_freq", 0.1)
GEMINI_API_URL = "https://api.generativeai.googleapis.com/v1beta2/models/gemini-2.5:generateText"

# ---------------- GEMINI FUNCTION ----------------
def generate_ai_response(prompt: str) -> str:
    headers = {"Authorization": f"Bearer {GEMINI_API_KEY}", "Content-Type": "application/json"}
    data = {"prompt": f"Respond as a Twitch bot with personality: {PERSONALITY}\n{prompt}",
            "temperature": 0.7,
            "maxOutputTokens": 300}
    try:
        resp = requests.post(GEMINI_API_URL, headers=headers, json=data)
        return resp.json()["candidates"][0]["content"].strip()
    except:
        return "Hmm… I couldn't come up with a response!"

# ---------------- MEMORY ----------------
def save_memory(user, message, response):
    try:
        with open(MEMORY_FILE) as f:
            memory = json.load(f)
    except:
        memory = {"chat_history": []}
    memory["chat_history"].append({"user": user, "message": message, "response": response})
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)

def get_recent_memory(n=5):
    try:
        with open(MEMORY_FILE) as f:
            memory = json.load(f)
        return memory["chat_history"][-n:]
    except:
        return []

# ---------------- DASHBOARD ----------------
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route("/")
def index():
    cfg = config
    return render_template("dashboard.html", config=cfg)

@socketio.on("update_config")
def handle_update(data):
    global PERSONALITY, AUTO_CHAT_FREQ
    for key, value in data.items():
        if key == "personality":
            PERSONALITY = value
            config["personality"] = value
        elif key == "auto_chat_freq":
            AUTO_CHAT_FREQ = value
            config["auto_chat_freq"] = value
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)
    emit("config_updated", config, broadcast=True)

@socketio.on("send_message")
def handle_send_message(data):
    msg = data.get("message")
    if msg:
        rewritten = generate_ai_response(f"Rewrite this in my personality: {msg}")
        asyncio.run_coroutine_threadsafe(bot.get_channel(CHANNEL).send(rewritten), asyncio.get_event_loop())

def run_dashboard():
    socketio.run(app, port=5000)

# ---------------- BOT ----------------
class GeminiTwitchBot(commands.Bot):
    def __init__(self):
        super().__init__(token=BOT_TOKEN, prefix="!", initial_channels=[CHANNEL])
        self.auto_chat_task.start()

    async def event_ready(self):
        print(f"Logged in as | {self.nick}")

    async def event_message(self, message):
        if message.author.name.lower() == BOT_USERNAME.lower():
            return
        await self.handle_commands(message)

    @commands.command(name="ai")
    async def ai_command(self, ctx):
        user_msg = ctx.message.content[len("!ai "):].strip()
        recent = get_recent_memory()
        context = "\n".join([f"{m['user']}: {m['message']}\nBot: {m['response']}" for m in recent])
        prompt = f"{context}\n{ctx.author.name} says: {user_msg}"
        response = generate_ai_response(prompt)
        save_memory(ctx.author.name, user_msg, response)
        await ctx.send(response)

    @commands.command(name="say")
    async def owner_say(self, ctx):
        if ctx.author.is_mod or ctx.author.name.lower() == CHANNEL.lower():
            msg = ctx.message.content[len("!say "):].strip()
            if msg:
                rewritten = generate_ai_response(f"Rewrite this in my personality: {msg}")
                await ctx.send(rewritten)
        else:
            await ctx.send("You don't have permission to use this command.")

    @tasks.loop(seconds=30)
    async def auto_chat_task(self):
        if random.random() < AUTO_CHAT_FREQ:
            channel = self.get_channel(CHANNEL)
            prompts = ["Say something funny", "Ask the viewers a question", "Share a quirky fact"]
            prompt = random.choice(prompts)
            response = generate_ai_response(prompt)
            await channel.send(response)

    async def event_usernotice(self, message):
        if message.tags.get("msg-id") == "sub":
            response = generate_ai_response(f"Welcome new subscriber {message.user.name}!")
        elif message.tags.get("msg-id") == "raid":
            response = generate_ai_response(f"Welcome raiders! {message.user.name} is leading the charge!")
        elif message.tags.get("msg-id") == "follow":
            response = generate_ai_response(f"Thanks for the follow {message.user.name}!")
        else:
            return
        await message.channel.send(response)

# ---------------- RUN EVERYTHING ----------------
if __name__ == "__main__":
    Thread(target=run_dashboard, daemon=True).start()
    bot = GeminiTwitchBot()
    bot.run()
