from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import json
from bot import generate_ai_response
from database import get_db_connection, set_favouritism_score

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
            moderation = json.dumps(config.get("moderation", {}))
            personality_traits = json.dumps(config.get("personality_traits", {}))
            delay_settings = json.dumps(config.get("delay_settings", {}))
            print(f"Socials: {socials}")
            print(f"Commands: {commands}")
            print(f"Moderation: {moderation}")
            print(f"Personality Traits: {personality_traits}")
            print(f"Delay Settings: {delay_settings}")
            return render_template("dashboard.html", personality=config["personality"], auto_chat_freq=config["auto_chat_freq"], socials=socials, commands=commands, moderation=moderation, personality_traits=personality_traits, delay_settings=delay_settings)
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
            config = load_config()
            rewritten = generate_ai_response(f"Rewrite this in my personality: {msg}", bot.nick, config)
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

    @socketio.on("update_moderation")
    def handle_update_moderation(data):
        print(f"Updating moderation with: {data}")
        config = load_config()
        config["moderation"] = data.get("moderation", config["moderation"])
        save_config(config)
        emit("config_updated", config, broadcast=True)
        # Update the bot's config as well
        bot.config["moderation"] = config["moderation"]

    @socketio.on("update_personality_traits")
    def handle_update_personality_traits(data):
        print(f"Updating personality traits with: {data}")
        config = load_config()
        config["personality_traits"] = data.get("personality_traits", config["personality_traits"])
        save_config(config)
        emit("config_updated", config, broadcast=True)
        # Update the bot's config as well
        bot.config["personality_traits"] = config["personality_traits"]

    @socketio.on("update_delay_settings")
    def handle_update_delay_settings(data):
        print(f"Updating delay settings with: {data}")
        config = load_config()
        config["delay_settings"] = data.get("delay_settings", config["delay_settings"])
        save_config(config)
        emit("config_updated", config, broadcast=True)
        # Update the bot's config as well
        bot.config["delay_settings"] = config["delay_settings"]

    @socketio.on("get_user_data")
    def handle_get_user_data():
        conn = get_db_connection()
        users = conn.execute("SELECT * FROM users").fetchall()
        conn.close()
        emit("user_data", {user["username"]: dict(user) for user in users})

    @socketio.on("update_favouritism_score")
    def handle_update_favouritism_score(data):
        username = data.get("username")
        score = data.get("score")
        if username is not None and score is not None:
            set_favouritism_score(username, score)
            handle_get_user_data() # Refresh the user data on the dashboard

    app.debug = True
    return app, socketio
