
import unittest
from unittest.mock import MagicMock, patch
import ai_client

class TestAIContext(unittest.TestCase):
    def setUp(self):
        self.config = {
            "gemini_api_key": "fake",
            "personality": "friendly",
            "channels": ["streamer_main", "other_channel"]
        }

    @patch('ai_client.get_user')
    @patch('requests.post')
    def test_context_attribution_with_channel(self, mock_post, mock_get_user):
        # Mock user data
        mock_get_user.return_value = {"favouritism_score": 0, "facts": "[]"}

        # Mock context monitor
        mock_context_monitor = MagicMock()
        mock_context_monitor.get_context.return_value = "This is spoken text."

        # Mock API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "candidates": [{"content": {"parts": [{"text": "Response"}]}}]
        }
        mock_post.return_value = mock_response

        # Call function
        ai_client.generate_ai_response("prompt", "user", self.config, context_monitor=mock_context_monitor)

        # Verify the prompt sent to API contains the attribution
        args, kwargs = mock_post.call_args
        json_data = kwargs['json']
        sent_text = json_data['contents'][0]['parts'][0]['text']

        self.assertIn("Recent spoken context (spoken by streamer_main):", sent_text)
        self.assertIn("This is spoken text.", sent_text)

    @patch('ai_client.get_user')
    @patch('requests.post')
    def test_context_attribution_default(self, mock_post, mock_get_user):
        # Config without channels
        config = {
            "gemini_api_key": "fake",
            "personality": "friendly"
        }

        mock_get_user.return_value = {"favouritism_score": 0, "facts": "[]"}

        mock_context_monitor = MagicMock()
        mock_context_monitor.get_context.return_value = "Spoken text."

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "candidates": [{"content": {"parts": [{"text": "Response"}]}}]
        }
        mock_post.return_value = mock_response

        ai_client.generate_ai_response("prompt", "user", config, context_monitor=mock_context_monitor)

        args, kwargs = mock_post.call_args
        json_data = kwargs['json']
        sent_text = json_data['contents'][0]['parts'][0]['text']

        self.assertIn("Recent spoken context (spoken by the streamer):", sent_text)

if __name__ == '__main__':
    unittest.main()
