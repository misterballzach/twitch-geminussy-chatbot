from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import json

CONFIG_FILE = "bot_config.json"

def create_dashboard_app(bot):
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'secret!'
    socketio = SocketIO(app, cors_allowed_origins="*")

    def load_config():
        with open(CONFIG_FILE) as f:
            return json.load(f)

    def save_config(config):
        print(f"Saving config: {config}")
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)

    @app.route("/")
    def index():
        try:
            config = load_config()
            print(f"Config: {config}")
            socials = json.dumps(config.get("socials", {}))
            commands = json.dumps(list(bot.commands.keys()))
            print(f"Socials: {socials}")
            print(f"Commands: {commands}")
            return render_template("dashboard.html", personality=config["personality"], auto_chat_freq=config["auto_chat_freq"], socials=socials, commands=commands)
        except Exception as e:
            print(f"Error in index route: {e}")
            return "Internal Server Error", 500

    @socketio.on("update_config")
    def handle_update(data):
        config = load_config()
        config["personality"] = data.get("personality", config["personality"])
        config["auto_chat_freq"] = data.get("auto_chat_freq", config["auto_chat_freq"])
        save_config(config)
        emit("config_updated", config, broadcast=True)
        # Update the bot's config as well
        bot.config["personality"] = config["personality"]
        bot.config["auto_chat_freq"] = config["auto_chat_freq"]


    @socketio.on("send_message")
    def handle_send_message(data):
        msg = data.get("message")
        if msg and bot:
            rewritten = bot.generate_ai_response(f"Rewrite this in my personality: {msg}")
            bot.send_message(rewritten)

    @socketio.on("update_socials")
    def handle_update_socials(data):
        print(f"Updating socials with: {data}")
        config = load_config()
        config["socials"] = data.get("socials", config["socials"])
        save_config(config)
        emit("config_updated", config, broadcast=True)
        # Update the bot's config as well
        bot.config["socials"] = config["socials"]

    app.debug = True
    return app, socketio
