import unittest
from connectk.game import ConnectKGame
from connectk.evaluate import Evaluator


class TestEvaluate(unittest.TestCase):
    def setUp(self):
        self.game = ConnectKGame(R=7, C=8, K=4, V=0, d=8)
        self.ev = Evaluator(self.game)

    def test_range_bounds(self):
        s = self.game.state_from_moves([3, 4, 3, 4, 3, 2])
        val = self.ev(s)
        self.assertGreaterEqual(val, -1.0)
        self.assertLessEqual(val, 1.0)

    def test_horizontal_symmetry(self):
        # Sol-sağ ayna simetrisinde Eval birebir aynı değeri vermeli
        s_left = self.game.state_from_moves([2, 3, 2])
        s_right = self.game.state_from_moves([5, 4, 5])
        self.assertAlmostEqual(self.ev(s_left), self.ev(s_right), places=9)

    def test_misere_sign_inversion(self):
        g_std = ConnectKGame(R=7, C=8, K=4, V=0, d=8)
        g_mis = ConnectKGame(R=7, C=8, K=4, V=2, d=8)
        ev_std = Evaluator(g_std)
        ev_mis = Evaluator(g_mis)
        s_std = g_std.state_from_moves([3, 0, 3, 0, 3])
        s_mis = g_mis.state_from_moves([3, 0, 3, 0, 3])
        self.assertAlmostEqual(ev_std(s_std), -ev_mis(s_mis), places=9)


if __name__ == "__main__":
    unittest.main()