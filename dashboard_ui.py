from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import json

CONFIG_FILE = "bot_config.json"

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

def load_config():
    with open(CONFIG_FILE) as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

@app.route("/")
def index():
    config = load_config()
    return render_template("dashboard.html", config=config)

@socketio.on("update_config")
def handle_update(data):
    config = load_config()
    for key, value in data.items():
        if key in config:
            config[key] = value
    save_config(config)
    emit("config_updated", config, broadcast=True)

@socketio.on("send_message")
def handle_send_message(data):
    """
    Emits message event to be picked up by bot for !say command
    """
    emit("bot_message", data, broadcast=True)

if __name__ == "__main__":
    socketio.run(app, port=5000)
