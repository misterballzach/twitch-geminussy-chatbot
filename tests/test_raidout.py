
import unittest
from unittest.mock import MagicMock, patch
import threading
import bot

class TestRaidOut(unittest.TestCase):
    def setUp(self):
        self.config = {
            "bot_username": "bot",
            "bot_token": "token",
            "channels": ["mychannel"],
            "gemini_api_key": "key",
            "personality": "friendly",
            "auto_chat_freq": 0.2
        }
        bot.MEMORY = {"chat_history": []}

        with patch('bot.TwitchEventSub'), \
             patch('bot.create_tables'), \
             patch('bot.IRCBot.connect_and_listen'), \
             patch('bot.IRCBot.auto_chat'), \
             patch('bot.IRCBot.conversation_starter_task'):
            self.bot = bot.IRCBot(self.config)
            self.bot.sock = MagicMock()
            self.bot.send_message = MagicMock()

    @patch('bot.requests.post')
    @patch('bot.requests.get')
    @patch('bot.generate_ai_response')
    def test_raidout_sequence_api_delayed(self, mock_ai, mock_get, mock_post):
        mock_ai.return_value = "Hype Message!"
        target_channel = "target_streamer"

        mock_get.side_effect = [
            MagicMock(json=lambda: {"client_id": "cid", "user_id": "uid", "scopes": []}),
            MagicMock(json=lambda: {"data": [{"id": "tid"}]}),
        ]
        mock_post.return_value.status_code = 200

        with patch('threading.Thread') as mock_thread, \
             patch('time.sleep') as mock_sleep: # Mock sleep to verify calls

            self.bot.raidout_command(target_channel, "broadcaster", "mychannel")

            # Execute task
            task = mock_thread.call_args[1]['target']
            task()

            # Verify 30s sleep was called
            # We expect multiple sleeps: one for 30s (propagation), one for 1s (pre-part)
            mock_sleep.assert_any_call(30)

            # Verify message sequence
            send_calls = self.bot.sock.send.call_args_list
            self.assertTrue(any(f"JOIN #{target_channel}".encode() in c[0][0] for c in send_calls))
            self.assertTrue(any(f"PRIVMSG #{target_channel} :Hype Message!".encode() in c[0][0] for c in send_calls))

if __name__ == '__main__':
    unittest.main()
