#!/bin/bash
# This script starts the Twitch AI Bot application.
# It ensures that the script is run from its own directory
# and installs dependencies before running the app.
cd "$(dirname "$0")"

echo "Installing required packages..."
pip install -r twitch_ai_bot/requirements.txt

echo "Starting the application..."
python twitch_ai_bot/main.py

# Pause to see output
read -p "Press Enter to exit..."
