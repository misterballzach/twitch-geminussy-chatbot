Gemini Twitch Bot

A Twitch chat bot powered by Google Gemini AI with personality, memory, and real-time dashboard control. Uses IRC to connect to Twitch and Flask + SocketIO for a lightweight web dashboard.

Features

Responds in chat with a defined personality.

Rewrites messages in your bot’s style (!say command).

Auto-chat with configurable frequency.

Maintains recent chat history for context-aware responses.

**Contextual Hearing:** Monitors a local caption file to understand spoken context from the streamer.

**Web Search:** Can perform Google searches to answer questions directly (!gemini command).

**Long-term Memory:** Learns and remembers facts about users (hobbies, location, etc.) over time.

Web dashboard to adjust personality and auto-chat frequency in real-time.

Logs all chat messages and bot responses in the console.

Requirements

Python 3.13+

Libraries: requests, flask, flask-socketio, eventlet

A Twitch OAuth token (from Twitch Token Generator
)

Google Gemini API key

(Optional) Google Custom Search API Key & Engine ID (for !gemini command)

(Optional) Path to a live caption/transcript text file (for contextual hearing)

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

(Optional) Google Search API Key & Engine ID

(Optional) Caption file path

Open the dashboard:

http://localhost:5000


Adjust the personality and auto-chat frequency in real-time.

Commands

!say <message> – Bot rewrites the message in its personality and sends it to chat.

!ai <message> – Bot generates a Gemini AI response with memory context.

!gemini <query> – Bot searches the web and answers the query directly (bypassing personality).

!brb – Puts the bot in "BRB Mode". It posts an AI summary of recent chat/captions and starts running games automatically.

!back – Returns the bot to normal mode.

Games

The bot features interactive chat games to keep the audience engaged. Games can be started manually with commands or run automatically during **BRB Mode**.

**1. Trivia (!trivia)**
*   **Description:** The bot generates a random trivia question using AI.
*   **How to Play:** Simply type your answer in the chat.
*   **Winning:** The bot checks if the correct answer is contained in your message. The first person to type the correct answer wins points!

**2. Guess the Number (!guess)**
*   **Description:** The bot selects a random number between 1 and 100.
*   **How to Play:** Type a number (e.g., "42") in the chat.
*   **Hints:** The bot will reply with "Higher! ⬆️" or "Lower! ⬇️" to guide you.
*   **Winning:** The first person to guess the exact number wins.

**3. Word Scramble (!scramble)**
*   **Description:** The bot shuffles the letters of a common streaming/gaming word (e.g., "keybaord").
*   **How to Play:** Type the unscrambled word in the chat.
*   **Winning:** The first person to type the correct word wins.

**4. Rock Paper Scissors (!rps)**
*   **Description:** A quick game against the bot.
*   **How to Play:** Type `!rps rock`, `!rps paper`, or `!rps scissors`.
*   **Winning:** The bot randomly picks a move and declares a winner or a tie.

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
    "channels": ["mrballzach"],
    "google_search_api_key": "AIzaSyYYYYYY",
    "google_search_engine_id": "0123456789",
    "caption_file_path": "C:/Stream/captions.txt"
}

License

MIT License – free to use and modify for personal or community projects.