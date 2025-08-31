import subprocess
import sys

def install_packages():
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

if __name__ == "__main__":
    print("Installing dependencies...")
    install_packages()
    print("All packages installed. You can now run twitch_gemini_bot.py")
