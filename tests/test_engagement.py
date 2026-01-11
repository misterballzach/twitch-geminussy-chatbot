
import sys
import os
import unittest
import threading
from unittest.mock import MagicMock, patch

# Mock sys.argv to avoid input prompts
sys.argv = ["bot.py"]

# Mock libraries before importing bot
sys.modules['socket'] = MagicMock()
sys.modules['ssl'] = MagicMock()
sys.modules['requests'] = MagicMock()

# Mock internal dependencies
mock_db = MagicMock()
sys.modules['database'] = mock_db

mock_ai = MagicMock()
mock_ai.generate_ai_response = MagicMock(return_value="AI Response")
sys.modules['ai_client'] = mock_ai

mock_games = MagicMock()
sys.modules['games'] = mock_games

import bot

class TestEngagement(unittest.TestCase):
    def setUp(self):
        self.config = {
            "bot_username": "bot",
            "bot_token": "token",
            "channels": ["test"],
            "gemini_api_key": "key",
            "personality": "friendly",
            "auto_chat_freq": 0.2
        }
        bot.MEMORY = {"chat_history": []}

        with patch('bot.create_tables'), \
             patch('bot.IRCBot.connect_and_listen'), \
             patch('bot.IRCBot.auto_chat'), \
             patch('bot.IRCBot.conversation_starter_task'):
            self.bot = bot.IRCBot(self.config)

        self.bot.send_message = MagicMock()

    def test_lurk_command(self):
        mock_ai.generate_ai_response.return_value = "Have a nice nap!"

        # Test needs to wait for thread
        with patch('threading.Thread') as mock_thread:
            self.bot.lurk_command("", "user1", "channel")

            # Verify a thread was started
            mock_thread.assert_called()
            # Manually run the target to verify logic
            target = mock_thread.call_args[1]['target']
            target()

        self.bot.send_message.assert_called_with("Have a nice nap!")
        args, _ = mock_ai.generate_ai_response.call_args
        self.assertIn("lurk mode", args[0])

    def test_raidmsg_command(self):
        mock_ai.generate_ai_response.return_value = "Raid Power!"

        with patch('threading.Thread') as mock_thread:
            self.bot.raidmsg_command("", "user1", "channel")
            mock_thread.assert_called()
            target = mock_thread.call_args[1]['target']
            target()

        self.bot.send_message.assert_called_with("Raid Power!")
        args, _ = mock_ai.generate_ai_response.call_args
        self.assertIn("hype raid message", args[0])

    def test_sub_welcome(self):
        line = "@msg-id=sub;display-name=NewSub :tmi.twitch.tv USERNOTICE #channel :Great stream!"
        mock_ai.generate_ai_response.return_value = "Thanks for the sub!"

        with patch('threading.Thread') as mock_thread:
            self.bot.handle_line(line)

            # Find the call that targets the welcome task
            # handle_line might start other threads (like fact extraction), so we need to be careful
            # But in this test environment, we just check if ANY thread was started with our logic

            # Since handle_line calls threading.Thread multiple times potentially,
            # we need to find the one that corresponds to our logic.
            # However, for simplicity in unit test, we can just grab the last call
            # or iterate to find the one calling generate_ai_response when executed.

            # Let's execute all thread targets to be safe
            for call in mock_thread.call_args_list:
                target = call[1].get('target')
                if target:
                    try:
                        target()
                    except:
                        pass

        self.bot.send_message.assert_called_with("Thanks for the sub!")

    def test_raid_welcome(self):
        line = "@msg-id=raid;display-name=Raider;msg-param-viewerCount=50 :tmi.twitch.tv USERNOTICE #channel"
        mock_ai.generate_ai_response.return_value = "Welcome raiders!"

        with patch('threading.Thread') as mock_thread:
            self.bot.handle_line(line)
            for call in mock_thread.call_args_list:
                target = call[1].get('target')
                if target:
                    try:
                        target()
                    except:
                        pass

        self.bot.send_message.assert_called_with("Welcome raiders!")

if __name__ == '__main__':
    unittest.main()
