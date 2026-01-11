
import unittest
from unittest.mock import MagicMock, patch
import json
import bot

class TestSentiment(unittest.TestCase):
    def setUp(self):
        self.config = {
            "personality_traits": {"likes": [], "dislikes": []},
            "gemini_api_key": "fake"
        }

    @patch('bot.generate_ai_response')
    def test_markdown_json(self, mock_ai):
        # AI returns markdown wrapped JSON
        mock_ai.return_value = "```json\n{\"sentiment\": \"positive\", \"topics\": [\"coding\"]}\n```"

        bot.analyze_sentiment_and_update_preferences("I love coding", "user1", self.config)

        self.assertIn("coding", self.config["personality_traits"]["likes"])

    @patch('bot.generate_ai_response')
    def test_plain_text_error(self, mock_ai):
        # AI returns error text
        mock_ai.return_value = "Hmm... I couldn't come up with a response!"

        # Should catch exception and log, not crash
        try:
            bot.analyze_sentiment_and_update_preferences("fail", "user1", self.config)
        except Exception:
            self.fail("analyze_sentiment_and_update_preferences raised Exception unexpectedly!")

if __name__ == '__main__':
    unittest.main()
