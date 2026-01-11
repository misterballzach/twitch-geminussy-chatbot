
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
    def test_raidout_sequence_api(self, mock_ai, mock_get, mock_post):
        mock_ai.return_value = "Hype Message!"
        target_channel = "target_streamer"

        # Mock validate_token
        mock_get.side_effect = [
            MagicMock(json=lambda: {"client_id": "cid", "user_id": "uid", "scopes": []}), # validate_token
            MagicMock(json=lambda: {"data": [{"id": "tid"}]}), # get_broadcaster_id (target)
        ]

        # Mock raid post
        mock_post.return_value.status_code = 200

        with patch('threading.Thread') as mock_thread, \
             patch('time.sleep'): # Skip sleeps

            self.bot.raidout_command(target_channel, "broadcaster", "mychannel")

            # Manually execute the task
            task = mock_thread.call_args[1]['target']
            task()

            # Verify AI generated message
            self.bot.send_message.assert_any_call("🚨 RAID INCOMING! Copy this: Hype Message!", "mychannel")

            # Verify API Raid call
            mock_post.assert_any_call(
                "https://api.twitch.tv/helix/raids?from_broadcaster_id=uid&to_broadcaster_id=tid",
                headers={"Client-ID": "cid", "Authorization": "Bearer token"},
                timeout=10
            )

            # Verify Invasion sequence (JOIN -> MSG -> PART) on socket
            send_calls = self.bot.sock.send.call_args_list
            self.assertTrue(any(f"JOIN #{target_channel}".encode() in c[0][0] for c in send_calls))
            self.assertTrue(any(f"PRIVMSG #{target_channel} :Hype Message!".encode() in c[0][0] for c in send_calls))

if __name__ == '__main__':
    unittest.main()
