@echo off
echo ===============================
echo Fixing TwitchClient installation...
echo ===============================

REM Uninstall all twitch-related packages
pip uninstall -y twitch twitchAPI twitch-python twitchio

REM Remove leftover twitch folders in site-packages
set SITEPACKAGES=%LocalAppData%\Programs\Python\Python313\Lib\site-packages

echo Deleting old twitch folders in %SITEPACKAGES%...
if exist "%SITEPACKAGES%\twitch" rd /s /q "%SITEPACKAGES%\twitch"
if exist "%SITEPACKAGES%\twitch-*.dist-info" rd /s /q "%SITEPACKAGES%\twitch-*.dist-info"

REM Reinstall the correct twitch-python package
pip install twitch-python==0.0.20

echo ===============================
echo Done! Test with:
echo python -c "from twitch import TwitchClient; print(TwitchClient)"
echo ===============================
pause
