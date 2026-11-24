import unittest
from connectk.game import ConnectKGame
from connectk.search import MinimaxAgent


class TestMinimax(unittest.TestCase):
    def setUp(self):
        # Öğrenci numarası sonu 08 -> (R=7, C=8, K=4, V=0, d=8)
        self.game = ConnectKGame(R=7, C=8, K=4, V=0, d=8)
        self.agent = MinimaxAgent(self.game)

    def test_depth2_node_count_empty_board(self):
        # Boş 7x8 tahtada derinlik 2 düğüm sayısı: 1 + 8 + 64 = 73
        s = self.game.initial_state()
        self.agent.choose_move(s, depth=2)
        self.assertEqual(self.agent.last_stats.nodes, 1 + 8 + 64)

    def test_win_in_one_move_max(self):
        # MAX'in 0, 1, 2 sütunlarında taşı var; 3. sütuna oynayınca kazanıyor
        s = self.game.state_from_moves([0, 7, 1, 7, 2, 7])
        move, val = self.agent.choose_move(s, depth=2)
        self.assertEqual(move, 3)
        self.assertEqual(val, 1.0)

    def test_block_opponent_win_in_one_move(self):
        # MIN 0, 1, 2 sütunlarında dikey 3'lü kurmuş; MAX 0. sütunu kapatmazsa kaybeder
        s = self.game.state_from_moves([3, 0, 4, 0, 5, 0])
        move, val = self.agent.choose_move(s, depth=2)
        self.assertEqual(move, 0)
        self.assertEqual(val, 0.0)

    def test_deterministic_choice(self):
        s = self.game.state_from_moves([3, 4, 3, 4])
        m1, v1 = self.agent.choose_move(s, depth=3)
        n1 = self.agent.last_stats.nodes
        m2, v2 = self.agent.choose_move(s, depth=3)
        n2 = self.agent.last_stats.nodes
        self.assertEqual((m1, v1, n1), (m2, v2, n2))


if __name__ == "__main__":
    unittest.main()