import math
from connectk.game import ConnectKGame, GameState, MAX_PLAYER, MIN_PLAYER, BLOCKED

# Varsayılan ağırlık vektörü: (w_k1_max, w_k1_min, w_k2_max, w_k2_min, w_center, w_variant)
DEFAULT_WEIGHTS = (12.0, -14.0, 3.0, -3.5, 1.2, 5.0)


class Evaluator:
    """
    Aşama 3: Önceden hesaplanmış pencereler ve varyant duyarlı değerlendirme fonksiyonu.
    Çıktıyı tanh ile (-1, +1) aralığına sıkıştırır.
    """

    def __init__(
        self,
        game: ConnectKGame,
        weights: tuple[float, ...] = DEFAULT_WEIGHTS,
        scale: float = 35.0,
    ):
        self.game = game
        self.weights = weights
        self.scale = scale
        self.windows, self.variant_window_flags = self._precompute_windows()

        # Merkez sütun indeksleri (C=8 için 3 ve 4)
        mid = game.C // 2
        if game.C % 2 == 0:
            self.center_cols = (mid - 1, mid)
        else:
            self.center_cols = (mid,)

    def _precompute_windows(
        self,
    ) -> tuple[tuple[tuple[tuple[int, int], ...], ...], tuple[bool, ...]]:
        """Tahtadaki tüm geçerli K-uzunluklu pencereleri bir kez listeler."""
        R, C, K, V = self.game.R, self.game.C, self.game.K, self.game.V
        init_board = self.game.initial_state().board
        directions = ((0, 1), (1, 0), (1, 1), (1, -1))

        windows: list[tuple[tuple[int, int], ...]] = []
        variant_flags: list[bool] = []
        seen: set[frozenset[tuple[int, int]]] = set()

        for r0 in range(R):
            for c0 in range(C):
                for dr, dc in directions:
                    cells: list[tuple[int, int]] = []
                    wrapped = False
                    valid = True
                    for step in range(K):
                        r = r0 + dr * step
                        raw_c = c0 + dc * step
                        if V == 1:
                            c = raw_c % C
                            if raw_c < 0 or raw_c >= C:
                                wrapped = True
                        else:
                            c = raw_c

                        if not (0 <= r < R and 0 <= c < C):
                            valid = False
                            break
                        if init_board[r][c] == BLOCKED:
                            valid = False
                            break
                        cells.append((r, c))

                    if not valid or len(cells) != K:
                        continue

                    key = frozenset(cells)
                    if key in seen:
                        continue
                    seen.add(key)
                    windows.append(tuple(cells))

                    # Varyant özel pencere işareti (V=1 sarmalı, V=3 engele komşu)
                    is_var = False
                    if V == 1 and wrapped:
                        is_var = True
                    elif V == 3:
                        for rr, cc in cells:
                            for nr in (rr - 1, rr, rr + 1):
                                for nc in (cc - 1, cc, cc + 1):
                                    if 0 <= nr < R and 0 <= nc < C and init_board[nr][nc] == BLOCKED:
                                        is_var = True
                    variant_flags.append(is_var)

        return tuple(windows), tuple(variant_flags)

    def extract_features(self, state: GameState) -> tuple[float, float, float, float, float, float]:
        """
        Konumdan 6 öznitelik çıkarır (sözlü kontrolünde elle de doğrulanabilir):
          f1: MAX için (K-1) taş + 1 boş pencere sayısı
          f2: MIN için (K-1) taş + 1 boş pencere sayısı
          f3: MAX için (K-2) taş + 2 boş pencere sayısı
          f4: MIN için (K-2) taş + 2 boş pencere sayısı
          f5: Merkez sütun kontrol farkı (MAX taşları - MIN taşları)
          f6: Varyant / yerçekimi destekli anında tamamlanabilir tehdit farkı
        """
        board = state.board
        R, C, K, V = self.game.R, self.game.C, self.game.K, self.game.V

        # Her sütunda yerçekimiyle taşın düşeceği ilk boş satırı bul (f6 için)
        playable_row = [-1] * C
        for c in range(C):
            for r in range(R):
                if board[r][c] == 0:
                    playable_row[c] = r
                else:
                    break

        f1 = f2 = f3 = f4 = f6 = 0.0

        for idx, win in enumerate(self.windows):
            max_cnt = 0
            min_cnt = 0
            empty_cell = None
            for r, c in win:
                val = board[r][c]
                if val == MAX_PLAYER:
                    max_cnt += 1
                elif val == MIN_PLAYER:
                    min_cnt += 1
                elif val == 0:
                    empty_cell = (r, c)

            # İki oyuncunun da taşı varsa pencere ölüdür
            if max_cnt > 0 and min_cnt > 0:
                continue

            if max_cnt == K - 1 and min_cnt == 0:
                f1 += 1.0
                if V in (1, 3) and self.variant_window_flags[idx]:
                    f6 += 1.0
                elif empty_cell is not None and playable_row[empty_cell[1]] == empty_cell[0]:
                    # Yerçekimiyle doğrudan erişilebilir tek hamlelik tehdit
                    f6 += 1.0
            elif min_cnt == K - 1 and max_cnt == 0:
                f2 += 1.0
                if V in (1, 3) and self.variant_window_flags[idx]:
                    f6 -= 1.0
                elif empty_cell is not None and playable_row[empty_cell[1]] == empty_cell[0]:
                    f6 -= 1.0
            elif max_cnt == K - 2 and min_cnt == 0:
                f3 += 1.0
            elif min_cnt == K - 2 and max_cnt == 0:
                f4 += 1.0

        # Merkez sütun kontrolü
        f5 = 0.0
        for c in self.center_cols:
            for r in range(R):
                v = board[r][c]
                if v == MAX_PLAYER:
                    f5 += 1.0
                elif v == MIN_PLAYER:
                    f5 -= 1.0

        return (f1, f2, f3, f4, f5, f6)

    def __call__(self, state: GameState) -> float:
        feats = self.extract_features(state)
        raw = sum(w * f for w, f in zip(self.weights, feats))
        # Misère (V=2) varyantında K'ya yaklaşmak tehlikeli olduğundan işaret tersine döner
        if self.game.V == 2:
            raw = -raw
        return math.tanh(raw / self.scale)