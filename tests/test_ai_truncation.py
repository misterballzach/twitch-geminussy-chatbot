
import unittest
from unittest.mock import MagicMock, patch
import ai_client

class TestAITruncation(unittest.TestCase):
    def setUp(self):
        self.config = {
            "gemini_api_key": "fake",
            "personality": "friendly",
            "max_response_length": 100 # Set low to test truncation removal
        }

    @patch('ai_client.get_user')
    @patch('requests.post')
    def test_no_hard_truncation(self, mock_post, mock_get_user):
        # Mock user data
        mock_get_user.return_value = {"favouritism_score": 0, "facts": "[]"}

        # Create a mock response object
        mock_response = MagicMock()
        long_text = "This is a very long response that exceeds the old hard limit but should now be returned in full so the bot can chunk it properly later." * 10

        # Structure it like the Gemini API response
        mock_response.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{"text": long_text}]
                }
            }]
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        # Call function
        result = ai_client.generate_ai_response("test prompt", "user", self.config)

        # Verify result is NOT truncated
        self.assertEqual(len(result), len(long_text))
        self.assertFalse(result.endswith("..."))
        self.assertEqual(result, long_text)

if __name__ == '__main__':
    unittest.main()
