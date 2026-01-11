
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

    @patch('bot.generate_ai_response')
    def test_raidout_sequence(self, mock_ai):
        mock_ai.return_value = "Hype Message!"
        target_channel = "target_streamer"

        with patch('threading.Thread') as mock_thread, \
             patch('time.sleep'): # Skip sleeps

            self.bot.raidout_command(target_channel, "broadcaster", "mychannel")

            # Verify thread started
            mock_thread.assert_called()

            # Manually execute the task
            task = mock_thread.call_args[1]['target']
            task()

            # Verify AI Generation
            args, _ = mock_ai.call_args
            self.assertIn("We are raiding", args[0])
            self.assertIn(target_channel, args[0])

            # Verify local chat messages
            self.bot.send_message.assert_any_call("🚨 RAID INCOMING! Copy this: Hype Message!", "mychannel")
            self.bot.send_message.assert_any_call(f"/raid {target_channel}", "mychannel")

            # Verify Invasion sequence (JOIN -> MSG -> PART) on socket
            # Note: We need to check send calls in order
            send_calls = self.bot.sock.send.call_args_list

            # 1. JOIN
            self.assertTrue(any(f"JOIN #{target_channel}".encode() in c[0][0] for c in send_calls))

            # 2. MSG
            self.assertTrue(any(f"PRIVMSG #{target_channel} :Hype Message!".encode() in c[0][0] for c in send_calls))

            # 3. PART
            self.assertTrue(any(f"PART #{target_channel}".encode() in c[0][0] for c in send_calls))

if __name__ == '__main__':
    unittest.main()
