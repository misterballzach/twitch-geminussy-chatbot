import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog
import os
import threading
import queue
import webbrowser
from dotenv import load_dotenv
from bot import Bot

class ChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Twitch AI Bot Control")
        self.root.geometry("600x600")

        self.message_queue = queue.Queue()
        self.rewrite_queue = queue.Queue()

        # Chat display
        self.chat_display = scrolledtext.ScrolledText(root, state='disabled', wrap=tk.WORD)
        self.chat_display.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Input frame
        input_frame = tk.Frame(root)
        input_frame.pack(padx=10, pady=10, fill=tk.X)

        self.user_input = tk.Entry(input_frame, width=70)
        self.user_input.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.send_button = tk.Button(input_frame, text="Send as AI", command=self.send_as_ai)
        self.send_button.pack(side=tk.RIGHT, padx=(5, 0))

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.start_bot()
        self.process_messages()

    def start_bot(self):
        load_dotenv(dotenv_path='twitch_ai_bot/.env')
        token = os.getenv("TWITCH_TOKEN")
        channel = os.getenv("TWITCH_CHANNEL")
        gemini_key = os.getenv("GEMINI_API_KEY")
        personality = os.getenv("AI_PERSONALITY")

        if not all([token, channel, gemini_key, personality]):
            messagebox.showerror("Error", "Configuration is missing. Please delete .env and restart.")
            self.root.destroy()
            return

        self.bot_thread = threading.Thread(target=self.run_bot_in_thread, args=(token, channel, personality, gemini_key), daemon=True)
        self.bot_thread.start()

    def run_bot_in_thread(self, token, channel, personality, gemini_key):
        bot = Bot(token, channel, personality, gemini_key, self.message_queue, self.rewrite_queue)
        bot.run()

    def process_messages(self):
        try:
            while not self.message_queue.empty():
                message = self.message_queue.get_nowait()
                self.chat_display.config(state='normal')
                self.chat_display.insert(tk.END, message + '\n')
                self.chat_display.config(state='disabled')
                self.chat_display.yview(tk.END)
        finally:
            self.root.after(100, self.process_messages)

    def send_as_ai(self):
        message = self.user_input.get()
        if message:
            self.rewrite_queue.put(message)
            self.user_input.delete(0, tk.END)

    def on_closing(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            # In a real app, you'd need a more graceful way to stop the bot thread
            self.root.destroy()
            os._exit(0) # Force exit since the bot thread is blocking


def setup_ui():
    """
    UI for initial configuration.
    """
    setup_root = tk.Tk()
    setup_root.title("Twitch AI Bot Setup")
    setup_root.geometry("450x450")

    def open_link(url):
        webbrowser.open_new(url)

    link_label = tk.Label(setup_root, text="Get your token here: https://twitchtokengenerator.com/", fg="blue", cursor="hand2")
    link_label.pack(pady=10)
    link_label.bind("<Button-1>", lambda e: open_link("https://twitchtokengenerator.com/"))

    tk.Label(setup_root, text="Twitch OAuth Token:").pack(pady=5)
    twitch_token_entry = tk.Entry(setup_root, width=50, show="*")
    twitch_token_entry.pack(pady=5)

    tk.Label(setup_root, text="Twitch Channel Name:").pack(pady=5)
    twitch_channel_entry = tk.Entry(setup_root, width=50)
    twitch_channel_entry.pack(pady=5)

    tk.Label(setup_root, text="Gemini API Key:").pack(pady=5)
    gemini_api_key_entry = tk.Entry(setup_root, width=50, show="*")
    gemini_api_key_entry.pack(pady=5)

    tk.Label(setup_root, text="AI Personality (e.g., 'a witty and sarcastic robot'):").pack(pady=5)
    ai_personality_entry = tk.Entry(setup_root, width=50)
    ai_personality_entry.pack(pady=5)

    def save_config_and_launch():
        if not all([twitch_token_entry.get(), twitch_channel_entry.get(), gemini_api_key_entry.get(), ai_personality_entry.get()]):
            messagebox.showerror("Error", "All fields are required.")
            return

        if not os.path.exists("twitch_ai_bot"):
            os.makedirs("twitch_ai_bot")

        with open("twitch_ai_bot/.env", "w") as f:
            f.write(f"TWITCH_TOKEN={twitch_token_entry.get()}\n")
            f.write(f"TWITCH_CHANNEL={twitch_channel_entry.get()}\n")
            f.write(f"GEMINI_API_KEY={gemini_api_key_entry.get()}\n")
            f.write(f"AI_PERSONALITY={ai_personality_entry.get()}\n")

        messagebox.showinfo("Success", "Configuration saved! Launching the bot control panel.")
        setup_root.destroy()
        main_app_window()

    tk.Button(setup_root, text="Save and Launch", command=save_config_and_launch).pack(pady=20)
    setup_root.mainloop()

def main_app_window():
    root = tk.Tk()
    app = ChatApp(root)
    root.mainloop()

if __name__ == "__main__":
    env_path = 'twitch_ai_bot/.env'
    if os.path.exists(env_path) and os.path.getsize(env_path) > 0:
        main_app_window()
    else:
        setup_ui()
