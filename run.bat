@echo off
REM This script starts the Twitch AI Bot application.
REM It changes the directory to the script's location and installs dependencies.
cd /d "%~dp0"

echo Installing required packages...
pip install -r twitch_ai_bot/requirements.txt

echo Starting the application...
python twitch_ai_bot/main.py

pause
