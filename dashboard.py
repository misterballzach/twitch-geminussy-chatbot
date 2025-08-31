from flask import Flask, request, jsonify
import json

CONFIG_FILE = "bot_config.json"
app = Flask(__name__)

def load_config():
    with open(CONFIG_FILE) as f:
        return json.load(f)

def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)

@app.route("/update", methods=["POST"])
def update_config():
    data = request.json
    config = load_config()
    for key in data:
        if key in config:
            config[key] = data[key]
    save_config(config)
    return jsonify({"status": "success", "new_config": config})

@app.route("/config", methods=["GET"])
def get_config():
    return jsonify(load_config())

if __name__ == "__main__":
    app.run(port=5000)
