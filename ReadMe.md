Gemini Twitch Bot

A Twitch chat bot powered by Google Gemini AI with personality, memory, and real-time dashboard control. Uses IRC to connect to Twitch and Flask + SocketIO for a lightweight web dashboard.

Features

Responds in chat with a defined personality.

Rewrites messages in your bot’s style (!say command).

Auto-chat with configurable frequency.

Maintains recent chat history for context-aware responses.

Web dashboard to adjust personality and auto-chat frequency in real-time.

Logs all chat messages and bot responses in the console.

Requirements

Python 3.13+

Libraries: requests, flask, flask-socketio, eventlet

A Twitch OAuth token (from Twitch Token Generator
)

Google Gemini API key

Installation

Clone or download the repository.

Install Python dependencies:

pip install requests flask flask-socketio eventlet


Ensure your Twitch OAuth token and Gemini API key are ready.

Usage

Run the bot:

python twitch_gemini_onefile.py


Follow the prompts to configure:

Bot username

Bot token (OAuth)

Gemini API key

Bot personality

Auto-chat frequency (0–1)

Twitch channels to join (comma-separated)

Open the dashboard:

http://localhost:5000


Adjust the personality and auto-chat frequency in real-time.

Commands

!say <message> – Bot rewrites the message in its personality and sends it to chat.

!ai <message> – Bot generates a Gemini AI response with memory context.

Notes

The bot logs all IRC activity to the console for transparency.

Auto-chat uses recent memory to generate contextually relevant responses.

If SSL issues occur, ensure your Python installation supports ssl (Windows: install pyopenssl if needed).

Example Config (bot_config.json)
{
    "bot_username": "tentaclehentie",
    "bot_token": "oauth:your_oauth_token",
    "gemini_api_key": "AIzaSyXXXXXX",
    "personality": "silly, goofy, old grandma",
    "auto_chat_freq": 0.5,
    "refresh_token": "your_refresh_token",
    "channels": ["mrballzach"]
}

License

MIT License – free to use and modify for personal or community projects.