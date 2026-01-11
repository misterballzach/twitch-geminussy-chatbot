
import unittest
from unittest.mock import MagicMock, patch
import json
import bot

class TestAds(unittest.TestCase):
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

        # Mock TwitchEventSub to prevent real connection
        with patch('bot.TwitchEventSub'), \
             patch('bot.create_tables'), \
             patch('bot.IRCBot.connect_and_listen'), \
             patch('bot.IRCBot.auto_chat'), \
             patch('bot.IRCBot.conversation_starter_task'):
            self.bot = bot.IRCBot(self.config)

        self.bot.send_message = MagicMock()
        self.bot.game_manager = MagicMock()
        self.bot.game_manager.start_random_game.return_value = "Game Started"

    @patch('bot.generate_ai_response')
    def test_start_ad_mode(self, mock_ai):
        mock_ai.return_value = "Ad Summary"

        # Call start_ad_mode directly
        with patch('threading.Thread') as mock_thread, \
             patch('threading.Timer') as mock_timer:

            self.bot.start_ad_mode("test_channel", 60)

            self.assertTrue(self.bot.is_ad_break)
            self.bot.send_message.assert_called_with("📺 Ad break started! For those stuck in ads, here's a quick summary of what's happening and a game! (Sub to skip ads!)")

            # Check if summary thread started
            found = False
            for call in mock_thread.call_args_list:
                if call.kwargs.get('target') == self.bot.send_brb_summary and call.kwargs.get('args') == ("test_channel", "System", "ad"):
                    found = True
                    break
            self.assertTrue(found, "Ad summary thread not started")

            # Check if end timer started
            found_timer = False
            for call in mock_timer.call_args_list:
                if call.args[0] == 60 and call.args[1] == self.bot.end_ad_mode:
                    found_timer = True
                    break
            self.assertTrue(found_timer, "End timer not started")

    def test_ad_game_loop(self):
        self.bot.is_ad_break = True

        with patch('threading.Timer') as mock_timer:
            self.bot.ad_game_loop("test_channel")

            self.bot.game_manager.start_random_game.assert_called_with("test_channel")
            self.bot.send_message.assert_called_with("Game Started")

            # Check recursive timer
            mock_timer.assert_called()
            args, _ = mock_timer.call_args
            self.assertEqual(args[0], 60)

if __name__ == '__main__':
    unittest.main()
