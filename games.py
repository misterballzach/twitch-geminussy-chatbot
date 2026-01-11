import random
import threading
import json
import time
from ai_client import generate_ai_response

class Game:
    def __init__(self, channel, config, send_message_callback=None):
        self.channel = channel
        self.config = config
        self.is_active = True
        self.winner = None
        self.send_message_callback = send_message_callback

    def check_answer(self, user, message):
        return False, None  # (is_correct, response_message)

    def end_game(self):
        self.is_active = False

class TriviaGame(Game):
    def __init__(self, channel, config, send_message_callback=None):
        super().__init__(channel, config, send_message_callback)
        self.question = ""
        self.answer = ""
        self.loading = True
        threading.Thread(target=self.fetch_question, daemon=True).start()

    def fetch_question(self):
        prompt = "Generate a single random trivia question and its answer. Return a JSON object with keys 'question' and 'answer'. The answer should be short (1-3 words). Only return the JSON."
        try:
            resp = generate_ai_response(prompt, "System", self.config)
            # Clean up markdown
            if resp.startswith("```json"): resp = resp[7:]
            if resp.startswith("```"): resp = resp[3:]
            if resp.endswith("```"): resp = resp[:-3]

            data = json.loads(resp.strip())
            self.question = data.get("question")
            self.answer = data.get("answer").lower().strip()
            print(f"[TRIVIA] Q: {self.question} A: {self.answer}")
        except Exception as e:
            print(f"[TRIVIA] Error fetching question: {e}")
            self.question = "Error fetching question. Type 'error' to end."
            self.answer = "error"

        self.loading = False
        if self.send_message_callback and self.is_active:
             self.send_message_callback(f"🎉 TRIVIA TIME! 🎉\nQuestion: {self.question}", self.channel)

    def get_start_message(self):
        return "⏳ Fetching a trivia question from the AI... Get ready!"

    def check_answer(self, user, message):
        if self.loading: return False, None
        if not self.is_active: return False, None

        # Simple containment check for flexibility, or exact match
        # Let's go with exact match or contained if answer is long
        cleaned_msg = message.lower().strip()
        if self.answer in cleaned_msg:
            self.winner = user
            self.end_game()
            return True, f"✅ Correct! @{user} got it right! The answer was: {self.answer}"
        return False, None

class GuessNumberGame(Game):
    def __init__(self, channel, config, send_message_callback=None):
        super().__init__(channel, config, send_message_callback)
        self.target = random.randint(1, 100)

    def get_start_message(self):
        return "🔢 GUESS THE NUMBER! 🔢\nI'm thinking of a number between 1 and 100. Type your guess!"

    def check_answer(self, user, message):
        if not self.is_active: return False, None

        try:
            guess = int(message.strip())
            if guess == self.target:
                self.winner = user
                self.end_game()
                return True, f"✅ Ding Ding! @{user} guessed the number {self.target} correctly!"
            elif guess < self.target:
                return False, "Higher! ⬆️"
            else:
                return False, "Lower! ⬇️"
        except ValueError:
            return False, None

class WordScrambleGame(Game):
    def __init__(self, channel, config, send_message_callback=None):
        super().__init__(channel, config, send_message_callback)
        self.word = ""
        self.scrambled = ""
        self.fetch_word()

    def fetch_word(self):
        # List of common words to avoid API latency for simple game
        words = ["twitch", "streamer", "chat", "moderator", "subscribe", "donate", "keyboard", "gaming", "python", "developer", "funny", "lorem", "ipsum", "controller", "screen", "camera", "lighting", "microphone", "headphones", "emote"]
        self.word = random.choice(words)
        l = list(self.word)
        random.shuffle(l)
        self.scrambled = "".join(l)

    def get_start_message(self):
        return f"🔤 WORD SCRAMBLE! 🔤\nUnscramble this word: {self.scrambled}"

    def check_answer(self, user, message):
        if not self.is_active: return False, None

        if message.lower().strip() == self.word:
            self.winner = user
            self.end_game()
            return True, f"✅ Nice! @{user} unscrambled the word: {self.word}"
        return False, None

class GameManager:
    def __init__(self, config, send_message_callback=None):
        self.config = config
        self.send_message_callback = send_message_callback
        self.active_games = {} # {channel: GameInstance}

    def start_game(self, game_type, channel, user):
        if channel in self.active_games and self.active_games[channel].is_active:
            return "A game is already active in this channel!"

        game = None
        if game_type == "trivia":
            game = TriviaGame(channel, self.config, self.send_message_callback)
        elif game_type == "guess":
            game = GuessNumberGame(channel, self.config, self.send_message_callback)
        elif game_type == "scramble":
            game = WordScrambleGame(channel, self.config, self.send_message_callback)
        else:
            return "Unknown game type."

        self.active_games[channel] = game
        return game.get_start_message()

    def handle_message(self, channel, user, message):
        if channel in self.active_games:
            game = self.active_games[channel]
            if not game.is_active:
                del self.active_games[channel]
                return None, 0

            is_correct, response = game.check_answer(user, message)
            points = 0

            if is_correct:
                points = 5 # 5 points for winning
                del self.active_games[channel]
            elif response and "Higher" in response or "Lower" in response:
                # Only return hints for number game occasionally or always?
                # Always is fine for chat engagement
                pass

            return response, points
        return None, 0

    def start_random_game(self, channel):
        game_types = ["trivia", "guess", "scramble"]
        selected = random.choice(game_types)
        return self.start_game(selected, channel, "System")
