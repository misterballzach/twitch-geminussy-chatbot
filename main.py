import asyncio
import threading
from bot import IRCBot, load_or_create_config
from dashboard import create_dashboard_app

if __name__ == "__main__":
    config = load_or_create_config()
    bot = IRCBot(config)

    app, socketio = create_dashboard_app(bot)

    def run_dashboard():
        socketio.run(app, port=5000, use_reloader=False)

    threading.Thread(target=run_dashboard, daemon=True).start()

    try:
        asyncio.get_event_loop().run_forever()
    except RuntimeError:
        asyncio.new_event_loop().run_forever()
