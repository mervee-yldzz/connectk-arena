from dataclasses import dataclass
import random

# Hücre sabitleri
EMPTY = 0        # Boş hücre
MAX_PLAYER = 1   # Bizim ajanımız (1. oyuncu)
MIN_PLAYER = -1  # Rakip ajan (2. oyuncu)
BLOCKED = 2      # V=3 varyantındaki engelli hücre


@dataclass(frozen=True)
class GameState:
    """
    Oyun durumunu değişmez (immutable) olarak tutar.
    frozen=True sayesinde oluşturulduktan sonra hiçbir alanı değiştirilemez.
    """
    board: tuple[tuple[int, ...], ...]
    to_move: int                    # Sıra kimde: MAX_PLAYER (1) veya MIN_PLAYER (-1)
    last_move: tuple[int, int] | None = None
    winner: int | None = None       # 1: MAX kazandı, -1: MIN kazandı, 0: Berabere, None: Devam ediyor


class ConnectKGame:
    """
    Connect-K oyun kuralları ve tüm varyasyonlar (V = 0, 1, 2, 3).
    """

    def __init__(self, R: int = 7, C: int = 8, K: int = 4, V: int = 0, d: int = 8):
        self.R = R
        self.C = C
        self.K = K
        self.V = V
        self.d = d

    def initial_state(self) -> GameState:
        """Boş başlangıç tahtasını oluşturur (V=3 ise 2 engelli hücre yerleştirir)."""
        grid = [[EMPTY for _ in range(self.C)] for _ in range(self.R)]

        if self.V == 3:
            rng = random.Random(self.d)
            blocked_cells = set()
            while len(blocked_cells) < 2:
                r = rng.randrange(self.R)
                c = rng.randrange(self.C)
                blocked_cells.add((r, c))
            for r, c in blocked_cells:
                grid[r][c] = BLOCKED

        board = tuple(tuple(row) for row in grid)
        # Eğer tüm sütunların en üstü kapalıysa oyun baştan beraberedir
        has_moves = any(board[0][c] == EMPTY for c in range(self.C))
        winner = None if has_moves else 0

        return GameState(board=board, to_move=MAX_PLAYER, last_move=None, winner=winner)

    def actions(self, state: GameState) -> list[int]:
        """Oynanabilecek yasal sütun numaralarını döndürür."""
        if state.winner is not None:
            return []
        # Bir sütunun en üst satırı (0. satır) boşsa o sütuna taş bırakılabilir
        return [c for c in range(self.C) if state.board[0][c] == EMPTY]

    def result(self, state: GameState, action: int) -> GameState:
        """
        Verilen sütuna (action) taş bırakır ve YENİ bir GameState döndürür.
        Mevcut state kesinlikle değiştirilmez.
        """
        if state.winner is not None:
            raise ValueError("Oyun zaten bitti, yeni hamle yapılamaz.")
        if action < 0 or action >= self.C or state.board[0][action] != EMPTY:
            raise ValueError(f"Geçersiz sütun hamlesi: {action}")

        # Yerçekimi: En üstten (0) aşağı doğru inerek ulaşılabilen en alt boş satırı bul.
        # V=3'te BLOCKED hücreye çarpınca durur, altındaki hücrelere hiç inemez.
        land_r = 0
        for r in range(self.R):
            if state.board[r][action] == EMPTY:
                land_r = r
            else:
                break

        player = state.to_move

        # Tahtayı kopyalayıp yeni taşı yerleştir ve tekrar değişmez tuple yap
        new_grid = [list(row) for row in state.board]
        new_grid[land_r][action] = player
        new_board = tuple(tuple(row) for row in new_grid)

        # Son konan taşın etrafında K'lık dizi oluştu mu?
        formed_k = self._check_k_in_a_row(new_board, land_r, action, player)

        if formed_k:
            # Misère (V=2) kuralında K taşı dizen oyuncu kaybeder!
            winner = -player if self.V == 2 else player
        elif not any(new_board[0][c] == EMPTY for c in range(self.C)):
            # Kimse K dizemedi ve tüm sütunlar dolduysa berabere
            winner = 0
        else:
            winner = None

        return GameState(
            board=new_board,
            to_move=-player,
            last_move=(land_r, action),
            winner=winner,
        )

    def is_terminal(self, state: GameState) -> bool:
        """Oyun bittiyse (kazanan varsa veya tahta dolduysa) True döndürür."""
        return state.winner is not None

    def utility(self, state: GameState) -> int:
        """MAX oyuncu gözüyle oyun sonu puanı: +1 (kazanç), 0 (beraberlik), -1 (kayıp)."""
        if state.winner is None:
            raise ValueError("Terminal olmayan durumun utility değeri istenemez.")
        return state.winner

    def _check_k_in_a_row(
        self, board: tuple[tuple[int, ...], ...], r0: int, c0: int, player: int
    ) -> bool:
        """Sadece son oynanan (r0, c0) hücresinin 4 ekseninde K taş dizildi mi kontrol eder."""
        directions = [
            (0, 1),   # Yatay
            (1, 0),   # Dikey
            (1, 1),   # Sağ aşağı çapraz
            (1, -1),  # Sol aşağı çapraz
        ]

        for dr, dc in directions:
            count = 1
            # İleri ve geri iki yönde aynı oyuncunun taşlarını say
            for sign in (1, -1):
                step = 1
                while count < self.K:
                    r = r0 + sign * dr * step
                    c = c0 + sign * dc * step

                    # Silindir varyantında (V=1) sütun indeksini yatayda başa sar
                    if self.V == 1:
                        c %= self.C

                    if not (0 <= r < self.R and 0 <= c < self.C):
                        break
                    if board[r][c] == player:
                        count += 1
                        step += 1
                    else:
                        # Boş hücre, rakip taş veya BLOCKED hücre diziyi keser
                        break

            if count >= self.K:
                return True

        return False

    def state_from_moves(self, moves: list[int] | str) -> GameState:
        """
        Kontrol noktalarındaki '3 3 4 4 5 5' formatındaki hamle dizisinden konum kurar.
        """
        if isinstance(moves, str):
            moves_list = [int(x) for x in moves.strip().split()] if moves.strip() else []
        else:
            moves_list = list(moves)

        state = self.initial_state()
        for col in moves_list:
            state = self.result(state, col)
        return state


def perft(game: ConnectKGame, state: GameState, depth: int) -> int:
    """
    Oyun modelinin sağlama testi: Belirli bir konumdan derinlik 'depth'e kadar
    budama yapmadan ulaşılan yaprak düğüm sayısını döndürür.
    """
    if depth == 0 or game.is_terminal(state):
        return 1
    return sum(perft(game, game.result(state, a), depth - 1) for a in game.actions(state))