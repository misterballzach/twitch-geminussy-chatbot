Gemini Twitch Bot

A Twitch chat bot powered by Google Gemini AI with personality, memory, and real-time dashboard control. Uses IRC to connect to Twitch and Flask + SocketIO for a lightweight web dashboard.

Features

### 🧠 Core AI Capabilities
*   **Personality Engine:** Responds in chat with a fully customizable personality (e.g., "silly grandma", "cyberpunk hacker").
*   **Contextual Hearing:** Monitors a live caption file to "hear" what the streamer is saying, allowing the bot to react to spoken context, not just chat text.
*   **Long-term Memory:** Learns and remembers permanent facts about users (e.g., "User X plays guitar", "User Y is from Canada") to make future conversations more personal.
*   **Web Search:** Uses Google Search to answer questions with up-to-date information (`!gemini <query>`).

### 🤝 Engagement & Automation
*   **Automatic Ad Detection:** Connects to Twitch EventSub to detect when ads start. The bot automatically posts a stream summary for non-subs and starts a game to keep them retained.
*   **BRB Mode (`!brb`):** When you step away, the bot takes over! It posts an AI-generated summary of recent chat/captions to catch everyone up and starts running games automatically.
*   **Smart Welcomes:**
    *   **Raids:** Greets incoming raiders with a hype, personality-driven welcome message.
    *   **Subs:** Thanks subscribers with a unique, enthusiastic AI response.
*   **Engagement Commands:**
    *   `!lurk`: Generates a friendly, funny send-off for lurkers.
    *   `!raidmsg`: Generates a hype "raid message" for your community to copy-paste when raiding out.

### 🎮 Chat Games
Built-in interactive games to boost engagement during downtime or ad breaks.
*   **Trivia:** AI-generated questions on any topic.
*   **Guess the Number:** Classic high/low guessing game.
*   **Word Scramble:** Unscramble streaming/gaming terms.
*   **Rock Paper Scissors:** Play against the bot.

Requirements

Python 3.13+

Libraries: `requests`, `flask`, `flask-socketio`, `eventlet`, `websocket-client`

A Twitch OAuth token (from [Twitch Token Generator](https://twitchtokengenerator.com))

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

**AI & Utility**
*   `!say <message>` – Bot rewrites the message in its personality and sends it to chat.
*   `!ai <message>` – Chat with the bot. It uses memory and context to reply.
*   `!gemini <query>` – Ask the bot to search the web (e.g., "Who won the game last night?").

**Stream Management**
*   `!brb` – Triggers "BRB Mode": Posts an AI recap of the last 30 messages/captions and runs games.
*   `!back` – Ends BRB Mode.
*   `!uptime` – Shows how long the stream has been live.
*   `!socials` – Posts your configured social media links.

**Fun & Engagement**
*   `!lurk` – Get a personalized "goodbye/lurk" message from the AI.
*   `!raidmsg` – Get a hype raid message to copy/paste.
*   `!roast <user>` – Ask the bot to lightly roast a user.
*   `!love <user>` – Check love compatibility (for fun).
*   `!8ball <question>` – Classic magic 8-ball answers.

**Games**
*   `!trivia` – Start a trivia question.
*   `!guess` – Start a "Guess the Number" game.
*   `!scramble` – Start a word scramble.
*   `!rps <move>` – Play Rock-Paper-Scissors.

Detailed Gameplay Guide

The bot features interactive chat games to keep the audience engaged. Games can be started manually with commands or run automatically during **BRB Mode** or **Ad Breaks**.

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