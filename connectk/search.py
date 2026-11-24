from dataclasses import dataclass
import math
import time
from typing import Callable
from connectk.game import ConnectKGame, GameState, MAX_PLAYER, MIN_PLAYER


@dataclass
class SearchStats:
    nodes: int = 0
    elapsed: float = 0.0
    depth_reached: int = 0


def default_eval(state: GameState) -> float:
    """Aşama 1 için geçici değerlendirme fonksiyonu: derinlik sınırında 0 döndürür."""
    return 0.0


def center_priority_key(col: int, C: int) -> tuple[float, int]:
    """Eşit değerli hamlelerde merkeze en yakın sütunu seçmek için sıralama anahtarı."""
    center = (C - 1) / 2.0
    return (abs(col - center), col)


class MinimaxAgent:
    """
    Aşama 1: Derinlik sınırlı Minimax arama ajanı.
    """

    def __init__(
        self,
        game: ConnectKGame,
        eval_fn: Callable[[GameState], float] = default_eval,
    ):
        self.game = game
        self.eval_fn = eval_fn
        self.nodes = 0
        self.last_stats = SearchStats()

    def choose_move(self, state: GameState, depth: int) -> tuple[int, float]:
        """
        Verilen konumdan 'depth' derinliğine kadar Minimax araması yapar.
        (en_iyi_sutun, kok_degeri) ikilisini döndürür.
        """
        legal_actions = self.game.actions(state)
        if not legal_actions:
            raise ValueError("Oynanabilecek yasal hamle yok.")

        t0 = time.perf_counter()
        self.nodes = 1  # Kök düğümü say

        # Eşitlik durumunda merkeze yakın olanın kazanması için adayları önce merkez sırasına diz
        ordered_actions = sorted(
            legal_actions, key=lambda c: center_priority_key(c, self.game.C)
        )

        best_action = ordered_actions[0]

        if state.to_move == MAX_PLAYER:
            best_value = -math.inf
            for action in ordered_actions:
                child = self.game.result(state, action)
                val = self.min_value(child, depth - 1)
                if val > best_value:
                    best_value = val
                    best_action = action
        else:
            best_value = math.inf
            for action in ordered_actions:
                child = self.game.result(state, action)
                val = self.max_value(child, depth - 1)
                if val < best_value:
                    best_value = val
                    best_action = action

        elapsed = time.perf_counter() - t0
        self.last_stats = SearchStats(
            nodes=self.nodes, elapsed=elapsed, depth_reached=depth
        )
        return best_action, best_value

    def max_value(self, state: GameState, depth: int) -> float:
        self.nodes += 1
        if self.game.is_terminal(state):
            return float(self.game.utility(state))
        if depth == 0:
            return float(self.eval_fn(state))

        v = -math.inf
        for action in self.game.actions(state):
            v = max(v, self.min_value(self.game.result(state, action), depth - 1))
        return v

    def min_value(self, state: GameState, depth: int) -> float:
        self.nodes += 1
        if self.game.is_terminal(state):
            return float(self.game.utility(state))
        if depth == 0:
            return float(self.eval_fn(state))

        v = math.inf
        for action in self.game.actions(state):
            v = min(v, self.max_value(self.game.result(state, action), depth - 1))
        return v