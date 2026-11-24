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
    ordering_time: float = 0.0


def default_eval(state: GameState) -> float:
    """Derinlik sınırında geçici değerlendirme fonksiyonu (Aşama 3'te gelişmiş Eval gelecek)."""
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
        legal_actions = self.game.actions(state)
        if not legal_actions:
            raise ValueError("Oynanabilecek yasal hamle yok.")

        t0 = time.perf_counter()
        self.nodes = 1

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


class AlphaBetaAgent:
    """
    Aşama 2: Alpha-Beta budaması ve hamle sıralaması destekli arama ajanı.
    ordering seçenekleri:
      - 'none'     : Sıralamasız (doğal sütun sırası: 0, 1, ..., C-1)
      - 'center'   : Merkezden dışarıya doğru
      - 'tactical' : Önce kazandıran / rakibi engelleyen hamle, sonra merkezden dışarı
    """

    def __init__(
        self,
        game: ConnectKGame,
        eval_fn: Callable[[GameState], float] = default_eval,
        ordering: str = "tactical",
    ):
        if ordering not in ("none", "center", "tactical"):
            raise ValueError(f"Geçersiz sıralama modu: {ordering}")
        self.game = game
        self.eval_fn = eval_fn
        self.ordering = ordering
        self.nodes = 0
        self.ordering_time = 0.0
        self.last_stats = SearchStats()

    def order_actions(self, state: GameState) -> list[int]:
        """Yasal hamleleri seçilen stratejiye göre sıralar ve sıralama süresini ölçer."""
        t_ord = time.perf_counter()
        actions = self.game.actions(state)

        if self.ordering == "none" or len(actions) <= 1:
            self.ordering_time += time.perf_counter() - t_ord
            return actions

        center_ordered = sorted(
            actions, key=lambda c: center_priority_key(c, self.game.C)
        )

        if self.ordering == "center":
            self.ordering_time += time.perf_counter() - t_ord
            return center_ordered

        # ordering == 'tactical': Önce kazandıran, sonra engelleyen hamleleri öne al
        player = state.to_move
        opponent = -player
        winning_moves: list[int] = []
        blocking_moves: list[int] = []
        rest_moves: list[int] = []

        # Rakibin sırasıymış gibi simüle etmek için geçici durum
        opp_turn_state = GameState(
            board=state.board,
            to_move=opponent,
            last_move=state.last_move,
            winner=state.winner,
        )

        for col in center_ordered:
            my_next = self.game.result(state, col)
            if my_next.winner == player:
                winning_moves.append(col)
                continue

            opp_next = self.game.result(opp_turn_state, col)
            if opp_next.winner == opponent:
                blocking_moves.append(col)
            else:
                rest_moves.append(col)

        result_order = winning_moves + blocking_moves + rest_moves
        self.ordering_time += time.perf_counter() - t_ord
        return result_order

    def choose_move(self, state: GameState, depth: int) -> tuple[int, float]:
        legal_actions = self.game.actions(state)
        if not legal_actions:
            raise ValueError("Oynanabilecek yasal hamle yok.")

        t0 = time.perf_counter()
        self.nodes = 1
        self.ordering_time = 0.0

        alpha = -math.inf
        beta = math.inf
        ordered_actions = self.order_actions(state)
        best_action = ordered_actions[0]

        if state.to_move == MAX_PLAYER:
            best_value = -math.inf
            for action in ordered_actions:
                child = self.game.result(state, action)
                val = self.min_value(child, depth - 1, alpha, beta)
                if val > best_value:
                    best_value = val
                    best_action = action
                alpha = max(alpha, best_value)
        else:
            best_value = math.inf
            for action in ordered_actions:
                child = self.game.result(state, action)
                val = self.max_value(child, depth - 1, alpha, beta)
                if val < best_value:
                    best_value = val
                    best_action = action
                beta = min(beta, best_value)

        elapsed = time.perf_counter() - t0
        self.last_stats = SearchStats(
            nodes=self.nodes,
            elapsed=elapsed,
            depth_reached=depth,
            ordering_time=self.ordering_time,
        )
        return best_action, best_value

    def max_value(self, state: GameState, depth: int, alpha: float, beta: float) -> float:
        self.nodes += 1
        if self.game.is_terminal(state):
            return float(self.game.utility(state))
        if depth == 0:
            return float(self.eval_fn(state))

        v = -math.inf
        for action in self.order_actions(state):
            v = max(v, self.min_value(self.game.result(state, action), depth - 1, alpha, beta))
            if v >= beta:
                return v
            alpha = max(alpha, v)
        return v

    def min_value(self, state: GameState, depth: int, alpha: float, beta: float) -> float:
        self.nodes += 1
        if self.game.is_terminal(state):
            return float(self.game.utility(state))
        if depth == 0:
            return float(self.eval_fn(state))

        v = math.inf
        for action in self.order_actions(state):
            v = min(v, self.max_value(self.game.result(state, action), depth - 1, alpha, beta))
            if v <= alpha:
                return v
            beta = min(beta, v)
        return v