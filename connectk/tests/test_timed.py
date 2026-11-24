import time
import unittest
from connectk.game import ConnectKGame
from connectk.evaluate import Evaluator
from connectk.search import AlphaBetaAgent, TimedAlphaBetaAgent


class TestTimedSearch(unittest.TestCase):
    def setUp(self):
        self.game = ConnectKGame(R=7, C=8, K=4, V=0, d=8)
        self.ev = Evaluator(self.game)

    def test_tt_matches_exact_alphabeta_value(self):
        ab = AlphaBetaAgent(self.game, eval_fn=self.ev, ordering="tactical")
        tt_agent = TimedAlphaBetaAgent(
            self.game, eval_fn=self.ev, use_tt=True, threat_extension=False, seed=8
        )
        for moves in ([3, 4, 3, 4], [3, 4, 2, 5, 3, 2], [0, 7, 1, 6, 2, 5]):
            s = self.game.state_from_moves(moves)
            _, val_ab = ab.choose_move(s, depth=4)
            _, val_tt = tt_agent.search_fixed_depth(s, depth=4)
            self.assertAlmostEqual(val_tt, val_ab, places=9)

    def test_strict_one_second_limit(self):
        agent = TimedAlphaBetaAgent(self.game, eval_fn=self.ev, use_tt=True, seed=8)
        s = self.game.state_from_moves([3, 4, 3, 4, 2, 5])
        t0 = time.perf_counter()
        move, _ = agent.choose_move(s, time_limit=1.0)
        elapsed = time.perf_counter() - t0
        self.assertIn(move, self.game.actions(s))
        self.assertLess(elapsed, 1.0)
        self.assertGreaterEqual(agent.last_stats.depth_reached, 1)


if __name__ == "__main__":
    unittest.main()