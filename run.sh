#!/bin/bash
# This script starts the Twitch AI Bot application.
# It ensures that the script is run from its own directory
# to resolve paths correctly.
cd "$(dirname "$0")"
python twitch_ai_bot/main.py

# Pause to see output
read -p "Press Enter to exit..."
