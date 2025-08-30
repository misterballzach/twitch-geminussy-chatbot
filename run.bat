@echo off
REM This script starts the Twitch AI Bot application.
REM It changes the directory to the script's location before running the app.
cd /d "%~dp0"
python twitch_ai_bot/main.py
pause
