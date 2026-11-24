import unittest
from connectk.game import ConnectKGame, MAX_PLAYER, MIN_PLAYER, BLOCKED, perft


class TestConnectKGame(unittest.TestCase):
    def setUp(self):
        # Öğrenci numarası sonu 08 -> (R=7, C=8, K=4, V=0, d=8)
        self.game = ConnectKGame(R=7, C=8, K=4, V=0, d=8)

    def test_variant_08_parameters(self):
        s = self.game.initial_state()
        self.assertEqual(len(s.board), 7)
        self.assertEqual(len(s.board[0]), 8)
        self.assertEqual(s.to_move, MAX_PLAYER)
        self.assertFalse(self.game.is_terminal(s))

    def test_perft_empty_board(self):
        s = self.game.initial_state()
        self.assertEqual(perft(self.game, s, 1), 8)
        self.assertEqual(perft(self.game, s, 2), 64)
        self.assertEqual(perft(self.game, s, 3), 512)

    def test_immutability(self):
        s0 = self.game.initial_state()
        s1 = self.game.result(s0, 3)
        self.assertEqual(s0.board[6][3], 0)
        self.assertEqual(s1.board[6][3], MAX_PLAYER)

    def test_full_column_removed_from_actions(self):
        # 7 satırlık 0. sütunu doldur (3 MAX, 3 MIN, 1 MAX -> 4'lü dizi oluşmaz)
        s = self.game.state_from_moves([0, 0, 0, 1, 0, 0, 0, 1, 0])
        self.assertNotIn(0, self.game.actions(s))
        self.assertEqual(len(self.game.actions(s)), 7)

    def test_win_horizontal(self):
        s = self.game.state_from_moves([0, 0, 1, 1, 2, 2, 3])
        self.assertTrue(self.game.is_terminal(s))
        self.assertEqual(self.game.utility(s), 1)

    def test_win_vertical(self):
        # MIN 0. sütunda dikey 4'lü yapar -> utility -1 olmalı
        s = self.game.state_from_moves([1, 0, 2, 0, 3, 0, 5, 0])
        self.assertTrue(self.game.is_terminal(s))
        self.assertEqual(self.game.utility(s), -1)

    def test_win_diagonal_rising(self):
        s = self.game.state_from_moves([0, 1, 1, 2, 3, 2, 2, 3, 4, 3, 3])
        self.assertTrue(self.game.is_terminal(s))
        self.assertEqual(self.game.utility(s), 1)

    def test_win_diagonal_falling(self):
        s = self.game.state_from_moves([7, 6, 6, 5, 4, 5, 5, 4, 3, 4, 4])
        self.assertTrue(self.game.is_terminal(s))
        self.assertEqual(self.game.utility(s), 1)

    def test_variant_cylinder_wrap(self):
        cyl_game = ConnectKGame(R=7, C=8, K=4, V=1, d=8)
        # 6, 7, 0, 1 sütunları yatayda sarılarak 4'lü oluşturur
        s = cyl_game.state_from_moves([6, 6, 7, 7, 0, 0, 1])
        self.assertTrue(cyl_game.is_terminal(s))
        self.assertEqual(cyl_game.utility(s), 1)

    def test_variant_misere_loses_on_k(self):
        misere_game = ConnectKGame(R=7, C=8, K=4, V=2, d=8)
        # MAX 4 taş dizer ama Misère kuralında dizen kaybeder (-1)
        s = misere_game.state_from_moves([0, 1, 0, 1, 0, 1, 0])
        self.assertTrue(misere_game.is_terminal(s))
        self.assertEqual(misere_game.utility(s), -1)

    def test_variant_blocked_cells(self):
        blocked_game = ConnectKGame(R=7, C=8, K=4, V=3, d=8)
        s = blocked_game.initial_state()
        # d=8 seed ile engelli hücreler (1, 5) ve (6, 2) olarak yerleşir
        self.assertEqual(s.board[1][5], BLOCKED)
        self.assertEqual(s.board[6][2], BLOCKED)
        # 2. sütunun en altı engelli olduğu için taş bir üstteki (5, 2) hücresine oturur
        s_after = blocked_game.result(s, 2)
        self.assertEqual(s_after.last_move, (5, 2))


if __name__ == "__main__":
    unittest.main()