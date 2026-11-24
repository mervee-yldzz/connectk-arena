import random
import unittest
from connectk.game import ConnectKGame
from connectk.search import MinimaxAgent, AlphaBetaAgent


class TestAlphaBeta(unittest.TestCase):
    def setUp(self):
        # Öğrenci numarası sonu 08 -> (R=7, C=8, K=4, V=0, d=8)
        self.game = ConnectKGame(R=7, C=8, K=4, V=0, d=8)
        self.mm = MinimaxAgent(self.game)

    def _random_non_terminal_states(self, count: int, seed: int = 8):
        rng = random.Random(seed)
        states = []
        while len(states) < count:
            s = self.game.initial_state()
            plies = rng.randint(4, 14)
            valid = True
            for _ in range(plies):
                acts = self.game.actions(s)
                if not acts or self.game.is_terminal(s):
                    valid = False
                    break
                s = self.game.result(s, rng.choice(acts))
            if valid and not self.game.is_terminal(s):
                states.append(s)
        return states

    def test_alphabeta_matches_minimax_value_and_move_quality(self):
        # Rastgele üretilen 15 konumda derinlik 4'te değer ve seçilen hamle kalitesi birebir aynı olmalı
        states = self._random_non_terminal_states(15, seed=8)
        for ordering in ("none", "center", "tactical"):
            ab = AlphaBetaAgent(self.game, ordering=ordering)
            for s in states:
                _, val_mm = self.mm.choose_move(s, depth=4)
                nodes_mm = self.mm.last_stats.nodes

                move_ab, val_ab = ab.choose_move(s, depth=4)
                nodes_ab = ab.last_stats.nodes

                # 1. Kök değerleri eşit olmalı
                self.assertEqual(val_ab, val_mm)
                # 2. Alpha-Beta hiçbir konumda Minimax'tan fazla düğüm gezmemeli
                self.assertLessEqual(nodes_ab, nodes_mm)
                # 3. Seçilen hamlenin gerçek Minimax değeri de kök değerine eşit olmalı
                child_ab = self.game.result(s, move_ab)
                if self.game.is_terminal(child_ab):
                    chosen_val = float(self.game.utility(child_ab))
                else:
                    chosen_val = self.mm.min_value(child_ab, depth=3)
                self.assertEqual(chosen_val, val_mm)

    def test_ordering_reduces_nodes_on_tactical_position(self):
        # Rakibin hemen kazanma tehdidi olduğu konumda taktiksel sıralama daha az düğüm gezmeli
        s = self.game.state_from_moves([3, 0, 4, 0, 5, 0])
        ab_none = AlphaBetaAgent(self.game, ordering="none")
        ab_tact = AlphaBetaAgent(self.game, ordering="tactical")

        ab_none.choose_move(s, depth=4)
        ab_tact.choose_move(s, depth=4)
        self.assertLessEqual(ab_tact.last_stats.nodes, ab_none.last_stats.nodes)


if __name__ == "__main__":
    unittest.main()