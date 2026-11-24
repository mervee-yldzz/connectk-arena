from dataclasses import dataclass
import math
import random
import time
from typing import Callable
from connectk.game import ConnectKGame, GameState, MAX_PLAYER, MIN_PLAYER, BLOCKED

EXACT = 0
LOWER = 1  # Beta kesmesinden gelen alt sınır
UPPER = 2  # Alpha'yı geçemeyen üst sınır


class SearchTimeout(Exception):
    """Zaman sınırı dolduğunda yarım kalan aramayı iptal etmek için fırlatılır."""


@dataclass
class SearchStats:
    nodes: int = 0
    elapsed: float = 0.0
    depth_reached: int = 0
    ordering_time: float = 0.0
    tt_hits: int = 0


@dataclass
class TTEntry:
    depth: int
    value: float
    flag: int
    best_move: int | None


def default_eval(state: GameState) -> float:
    return 0.0


def center_priority_key(col: int, C: int) -> tuple[float, int]:
    center = (C - 1) / 2.0
    return (abs(col - center), col)


class MinimaxAgent:
    """Aşama 1: Derinlik sınırlı Minimax arama ajanı."""

    def __init__(self, game: ConnectKGame, eval_fn: Callable[[GameState], float] = default_eval):
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
        ordered_actions = sorted(legal_actions, key=lambda c: center_priority_key(c, self.game.C))
        best_action = ordered_actions[0]

        if state.to_move == MAX_PLAYER:
            best_value = -math.inf
            for action in ordered_actions:
                val = self.min_value(self.game.result(state, action), depth - 1)
                if val > best_value:
                    best_value = val
                    best_action = action
        else:
            best_value = math.inf
            for action in ordered_actions:
                val = self.max_value(self.game.result(state, action), depth - 1)
                if val < best_value:
                    best_value = val
                    best_action = action

        self.last_stats = SearchStats(
            nodes=self.nodes, elapsed=time.perf_counter() - t0, depth_reached=depth
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
    """Aşama 2: Alpha-Beta budaması ve hamle sıralaması destekli arama ajanı."""

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
        t_ord = time.perf_counter()
        actions = self.game.actions(state)
        if self.ordering == "none" or len(actions) <= 1:
            self.ordering_time += time.perf_counter() - t_ord
            return actions

        center_ordered = sorted(actions, key=lambda c: center_priority_key(c, self.game.C))
        if self.ordering == "center":
            self.ordering_time += time.perf_counter() - t_ord
            return center_ordered

        player = state.to_move
        opponent = -player
        winning_moves: list[int] = []
        blocking_moves: list[int] = []
        rest_moves: list[int] = []

        opp_turn_state = GameState(
            board=state.board,
            to_move=opponent,
            last_move=state.last_move,
            winner=state.winner,
        )

        for col in center_ordered:
            if self.game.result(state, col).winner == player:
                winning_moves.append(col)
                continue
            if self.game.result(opp_turn_state, col).winner == opponent:
                blocking_moves.append(col)
            else:
                rest_moves.append(col)

        res = winning_moves + blocking_moves + rest_moves
        self.ordering_time += time.perf_counter() - t_ord
        return res

    def choose_move(self, state: GameState, depth: int) -> tuple[int, float]:
        legal_actions = self.game.actions(state)
        if not legal_actions:
            raise ValueError("Oynanabilecek yasal hamle yok.")

        t0 = time.perf_counter()
        self.nodes = 1
        self.ordering_time = 0.0
        alpha, beta = -math.inf, math.inf
        ordered_actions = self.order_actions(state)
        best_action = ordered_actions[0]

        if state.to_move == MAX_PLAYER:
            best_value = -math.inf
            for action in ordered_actions:
                val = self.min_value(self.game.result(state, action), depth - 1, alpha, beta)
                if val > best_value:
                    best_value = val
                    best_action = action
                alpha = max(alpha, best_value)
        else:
            best_value = math.inf
            for action in ordered_actions:
                val = self.max_value(self.game.result(state, action), depth - 1, alpha, beta)
                if val < best_value:
                    best_value = val
                    best_action = action
                beta = min(beta, best_value)

        self.last_stats = SearchStats(
            nodes=self.nodes,
            elapsed=time.perf_counter() - t0,
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


class TimedAlphaBetaAgent:
    """
    Aşama 4: İteratif derinleşme, Zobrist anahtarlı Yer Değiştirme Tablosu (TT)
    ve acil tehdit derinlik uzatması (ufuk etkisi çözümü) içeren zaman sınırlı ajan.
    """

    def __init__(
        self,
        game: ConnectKGame,
        eval_fn: Callable[[GameState], float] = default_eval,
        use_tt: bool = True,
        threat_extension: bool = True,
        seed: int = 8,
    ):
        self.game = game
        self.eval_fn = eval_fn
        self.use_tt = use_tt
        self.threat_extension = threat_extension
        self.seed = seed

        rng = random.Random(seed)
        self.zobrist_table = {
            (r, c, piece): rng.getrandbits(64)
            for r in range(game.R)
            for c in range(game.C)
            for piece in (MAX_PLAYER, MIN_PLAYER, BLOCKED)
        }
        self.zobrist_turn = rng.getrandbits(64)
        self.tt: dict[int, TTEntry] = {}

        self.nodes = 0
        self.tt_hits = 0
        self.deadline = math.inf
        self.last_stats = SearchStats()

    def compute_zobrist(self, state: GameState) -> int:
        h = 0
        for r in range(self.game.R):
            for c in range(self.game.C):
                piece = state.board[r][c]
                if piece != 0:
                    h ^= self.zobrist_table[(r, c, piece)]
        if state.to_move == MIN_PLAYER:
            h ^= self.zobrist_turn
        return h

    def _has_immediate_threat(self, state: GameState) -> bool:
        """Rakibin tek hamlede kazanma tehdidi varsa True döndürür (ufuk etkisi koruması)."""
        if self.game.V == 2:
            return False
        opponent = -state.to_move
        opp_state = GameState(
            board=state.board,
            to_move=opponent,
            last_move=state.last_move,
            winner=state.winner,
        )
        for col in self.game.actions(opp_state):
            if self.game.result(opp_state, col).winner == opponent:
                return True
        return False

    def _order_actions(self, state: GameState, priority_move: int | None = None) -> list[int]:
        actions = self.game.actions(state)
        if len(actions) <= 1:
            return actions

        center_ordered = sorted(actions, key=lambda c: center_priority_key(c, self.game.C))
        player = state.to_move
        opponent = -player
        winning: list[int] = []
        blocking: list[int] = []
        rest: list[int] = []

        opp_state = GameState(
            board=state.board,
            to_move=opponent,
            last_move=state.last_move,
            winner=state.winner,
        )

        for col in center_ordered:
            if col == priority_move:
                continue
            if self.game.result(state, col).winner == player:
                winning.append(col)
            elif self.game.result(opp_state, col).winner == opponent:
                blocking.append(col)
            else:
                rest.append(col)

        ordered = winning + blocking + rest
        if priority_move is not None and priority_move in actions:
            ordered = [priority_move] + ordered
        return ordered

    def _check_timeout(self) -> None:
        # Süre kontrolü her 1000 düğümde bir yapılır (perf_counter maliyetini düşürür)
        if self.nodes % 1000 == 0 and time.perf_counter() >= self.deadline:
            raise SearchTimeout()

    def _alphabeta_tt(
        self,
        state: GameState,
        depth: int,
        alpha: float,
        beta: float,
        zhash: int,
        ext_left: int,
    ) -> float:
        self.nodes += 1
        self._check_timeout()

        if self.game.is_terminal(state):
            return float(self.game.utility(state))

        if depth == 0:
            if self.threat_extension and ext_left > 0 and self._has_immediate_threat(state):
                depth = 1
                ext_left -= 1
            else:
                return float(self.eval_fn(state))

        alpha_orig = alpha
        beta_orig = beta
        tt_move: int | None = None

        if self.use_tt and zhash in self.tt:
            entry = self.tt[zhash]
            tt_move = entry.best_move
            if entry.depth >= depth:
                self.tt_hits += 1
                if entry.flag == EXACT:
                    return entry.value
                elif entry.flag == LOWER:
                    alpha = max(alpha, entry.value)
                elif entry.flag == UPPER:
                    beta = min(beta, entry.value)
                if alpha >= beta:
                    return entry.value

        ordered_actions = self._order_actions(state, priority_move=tt_move)
        best_move = ordered_actions[0]
        player = state.to_move

        if player == MAX_PLAYER:
            v = -math.inf
            for action in ordered_actions:
                child = self.game.result(state, action)
                r_land, c_land = child.last_move  # type: ignore
                child_hash = (
                    zhash
                    ^ self.zobrist_table[(r_land, c_land, player)]
                    ^ self.zobrist_turn
                )
                score = self._alphabeta_tt(child, depth - 1, alpha, beta, child_hash, ext_left)
                if score > v:
                    v = score
                    best_move = action
                alpha = max(alpha, v)
                if v >= beta:
                    break
        else:
            v = math.inf
            for action in ordered_actions:
                child = self.game.result(state, action)
                r_land, c_land = child.last_move  # type: ignore
                child_hash = (
                    zhash
                    ^ self.zobrist_table[(r_land, c_land, player)]
                    ^ self.zobrist_turn
                )
                score = self._alphabeta_tt(child, depth - 1, alpha, beta, child_hash, ext_left)
                if score < v:
                    v = score
                    best_move = action
                beta = min(beta, v)
                if v <= alpha:
                    break

        if self.use_tt:
            if v <= alpha_orig:
                flag = UPPER
            elif v >= beta_orig:
                flag = LOWER
            else:
                flag = EXACT
            self.tt[zhash] = TTEntry(depth=depth, value=v, flag=flag, best_move=best_move)

        return v

    def search_fixed_depth(self, state: GameState, depth: int) -> tuple[int, float]:
        """Belirli bir sabit derinlikte kök araması yapar (TT doğrulama ve ufuk testleri için)."""
        legal_actions = self.game.actions(state)
        if not legal_actions:
            raise ValueError("Oynanabilecek yasal hamle yok.")

        t0 = time.perf_counter()
        self.nodes = 1
        self.tt_hits = 0
        self.deadline = math.inf

        root_hash = self.compute_zobrist(state)
        tt_move = self.tt[root_hash].best_move if (self.use_tt and root_hash in self.tt) else None
        ordered_actions = self._order_actions(state, priority_move=tt_move)

        best_action = ordered_actions[0]
        alpha, beta = -math.inf, math.inf
        player = state.to_move
        ext_budget = 1 if self.threat_extension else 0

        if player == MAX_PLAYER:
            best_val = -math.inf
            for action in ordered_actions:
                child = self.game.result(state, action)
                r_land, c_land = child.last_move  # type: ignore
                child_hash = root_hash ^ self.zobrist_table[(r_land, c_land, player)] ^ self.zobrist_turn
                val = self._alphabeta_tt(child, depth - 1, alpha, beta, child_hash, ext_budget)
                if val > best_val:
                    best_val = val
                    best_action = action
                alpha = max(alpha, best_val)
        else:
            best_val = math.inf
            for action in ordered_actions:
                child = self.game.result(state, action)
                r_land, c_land = child.last_move  # type: ignore
                child_hash = root_hash ^ self.zobrist_table[(r_land, c_land, player)] ^ self.zobrist_turn
                val = self._alphabeta_tt(child, depth - 1, alpha, beta, child_hash, ext_budget)
                if val < best_val:
                    best_val = val
                    best_action = action
                beta = min(beta, best_val)

        if self.use_tt:
            self.tt[root_hash] = TTEntry(depth=depth, value=best_val, flag=EXACT, best_move=best_action)

        self.last_stats = SearchStats(
            nodes=self.nodes,
            elapsed=time.perf_counter() - t0,
            depth_reached=depth,
            tt_hits=self.tt_hits,
        )
        return best_action, best_val

    def choose_move(self, state: GameState, time_limit: float = 1.0, max_depth: int = 42) -> tuple[int, float]:
        """
        İteratif derinleşme ile süre dolana kadar en iyi hamleyi arar.
        Süre dolduğunda yarım kalan derinliği atıp son tamamlanan derinliğin hamlesini döndürür.
        """
        legal_actions = self.game.actions(state)
        if not legal_actions:
            raise ValueError("Oynanabilecek yasal hamle yok.")

        t0 = time.perf_counter()
        # Çöp toplayıcı ve I/O gecikmeleri için 60 ms güvenlik payı bırakılır
        safe_budget = max(0.02, time_limit - 0.06)
        self.deadline = t0 + safe_budget
        self.nodes = 0
        self.tt_hits = 0

        ordered_initial = self._order_actions(state)
        best_action = ordered_initial[0]
        best_value = 0.0
        completed_depth = 0
        root_hash = self.compute_zobrist(state)
        ext_budget = 1 if self.threat_extension else 0

        for depth in range(1, max_depth + 1):
            if time.perf_counter() >= self.deadline:
                break
            try:
                iter_actions = self._order_actions(state, priority_move=best_action if completed_depth > 0 else None)
                alpha, beta = -math.inf, math.inf
                player = state.to_move

                if player == MAX_PLAYER:
                    curr_best_val = -math.inf
                    curr_best_act = iter_actions[0]
                    for action in iter_actions:
                        self.nodes += 1
                        self._check_timeout()
                        child = self.game.result(state, action)
                        r_land, c_land = child.last_move  # type: ignore
                        child_hash = root_hash ^ self.zobrist_table[(r_land, c_land, player)] ^ self.zobrist_turn
                        val = self._alphabeta_tt(child, depth - 1, alpha, beta, child_hash, ext_budget)
                        if val > curr_best_val:
                            curr_best_val = val
                            curr_best_act = action
                        alpha = max(alpha, curr_best_val)
                else:
                    curr_best_val = math.inf
                    curr_best_act = iter_actions[0]
                    for action in iter_actions:
                        self.nodes += 1
                        self._check_timeout()
                        child = self.game.result(state, action)
                        r_land, c_land = child.last_move  # type: ignore
                        child_hash = root_hash ^ self.zobrist_table[(r_land, c_land, player)] ^ self.zobrist_turn
                        val = self._alphabeta_tt(child, depth - 1, alpha, beta, child_hash, ext_budget)
                        if val < curr_best_val:
                            curr_best_val = val
                            curr_best_act = action
                        beta = min(beta, curr_best_val)

                best_action = curr_best_act
                best_value = curr_best_val
                completed_depth = depth

                if self.use_tt:
                    self.tt[root_hash] = TTEntry(depth=depth, value=best_value, flag=EXACT, best_move=best_action)

                # Kesin kazanç veya kesin kayıp bulunduysa daha derine inmeye gerek yok
                if abs(best_value) == 1.0:
                    break
            except SearchTimeout:
                # Yarım kalan derinlik atılır; son tamamlanan derinliğin hamlesi korunur
                break

        self.last_stats = SearchStats(
            nodes=self.nodes,
            elapsed=time.perf_counter() - t0,
            depth_reached=completed_depth,
            tt_hits=self.tt_hits,
        )
        return best_action, best_value