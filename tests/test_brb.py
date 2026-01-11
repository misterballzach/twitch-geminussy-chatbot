
import sys
import os
import unittest
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
mock_ai.generate_ai_response = MagicMock(return_value="Summary of chat")
sys.modules['ai_client'] = mock_ai

mock_games = MagicMock()
sys.modules['games'] = mock_games

# Now import bot
import bot

class TestBRB(unittest.TestCase):
    def setUp(self):
        self.config = {
            "bot_username": "bot",
            "bot_token": "token",
            "channels": ["test"],
            "gemini_api_key": "key",
            "personality": "friendly",
            "auto_chat_freq": 0.2
        }
        # Reset memory
        bot.MEMORY = {"chat_history": []}

        # Initialize bot with mocked dependencies
        with patch('bot.create_tables'), \
             patch('bot.IRCBot.connect_and_listen'), \
             patch('bot.IRCBot.auto_chat'), \
             patch('bot.IRCBot.conversation_starter_task'):
            self.bot = bot.IRCBot(self.config)

        # Mock send_message to capture output
        self.bot.send_message = MagicMock()
        # Mock brb_game_loop to verify calls
        self.bot.brb_game_loop = MagicMock()

    def test_send_brb_summary_starts_game_if_active(self):
        # Set BRB active
        self.bot.is_brb = True

        # Call the method directly
        self.bot.send_brb_summary("test_channel", "broadcaster")

        # Verify generate_ai_response was called
        mock_ai.generate_ai_response.assert_called()

        # Verify send_message was called with the response
        self.bot.send_message.assert_called_with("Summary of chat")

        # Verify game loop started
        self.bot.brb_game_loop.assert_called_with("test_channel")

    def test_send_brb_summary_stops_if_inactive(self):
        # Set BRB inactive
        self.bot.is_brb = False

        self.bot.send_brb_summary("test_channel", "broadcaster")

        # Verify message NOT sent
        self.bot.send_message.assert_not_called()

        # Verify game loop NOT started
        self.bot.brb_game_loop.assert_not_called()

    def test_brb_command_only_starts_summary_thread(self):
        with patch('threading.Thread') as mock_thread, \
             patch('threading.Timer') as mock_timer:
            self.bot.brb_command("", "broadcaster", "test_channel")

            # Verify brb_game_loop NOT called directly
            self.bot.brb_game_loop.assert_not_called()

            # Check if thread was started for send_brb_summary
            found = False
            for call in mock_thread.call_args_list:
                if call.kwargs.get('target') == self.bot.send_brb_summary:
                    found = True
                    break
            self.assertTrue(found, "send_brb_summary thread not started")

if __name__ == '__main__':
    unittest.main()
