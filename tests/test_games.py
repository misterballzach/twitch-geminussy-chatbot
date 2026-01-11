
import unittest
from unittest.mock import MagicMock
from games import GameManager, TriviaGame, GuessNumberGame, WordScrambleGame

class TestGames(unittest.TestCase):
    def setUp(self):
        self.config = {"gemini_api_key": "fake"}
        self.callback = MagicMock()
        self.manager = GameManager(self.config, self.callback)

    def test_init_games(self):
        # Test explicit initialization
        g1 = TriviaGame("ch", self.config, self.callback)
        g2 = GuessNumberGame("ch", self.config, self.callback)
        g3 = WordScrambleGame("ch", self.config, self.callback)

        self.assertIsNotNone(g1)
        self.assertIsNotNone(g2)
        self.assertIsNotNone(g3)

    def test_start_games_via_manager(self):
        # Test manager spawning (which was failing)
        self.manager.active_games = {}
        self.manager.start_game("guess", "ch1", "user")
        self.assertIsInstance(self.manager.active_games["ch1"], GuessNumberGame)

        self.manager.active_games = {}
        self.manager.start_game("scramble", "ch2", "user")
        self.assertIsInstance(self.manager.active_games["ch2"], WordScrambleGame)

if __name__ == '__main__':
    unittest.main()
