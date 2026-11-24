import csv
import os
import random
import struct
import time
import zlib
from connectk.game import ConnectKGame, perft
from connectk.search import MinimaxAgent, AlphaBetaAgent


def _save_bar_chart_png(filename: str, labels: list[str], values: list[float]) -> None:
    """Harici kütüphane gerektirmeden Aşama 2 düğüm karşılaştırma grafiğini PNG olarak çizer."""
    try:
        import matplotlib.pyplot as plt  # type: ignore

        plt.figure(figsize=(8, 4.8))
        colors = ["#64748b", "#3b82f6", "#10b981", "#f59e0b"]
        bars = plt.bar(labels, values, color=colors[: len(labels)], width=0.55)
        plt.ylabel("Ortalama Düğüm Sayısı (Derinlik 6)")
        plt.title("Aşama 2: Minimax vs Alpha-Beta Hamle Sıralaması (50 Konum, d=08)")
        for bar, val in zip(bars, values):
            plt.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height(),
                f"{val:,.1f}",
                ha="center",
                va="bottom",
                fontsize=9,
            )
        plt.tight_layout()
        plt.savefig(filename, dpi=150)
        plt.close()
        return
    except ImportError:
        pass

    # Saf Python yedek PNG çizici
    w, h = 720, 420
    bg = (255, 255, 255)
    axis_col = (50, 50, 50)
    bar_colors = [(100, 116, 139), (59, 130, 246), (16, 185, 129), (245, 158, 11)]
    pixels = bytearray(bg * (w * h))

    def set_px(x: int, y: int, col: tuple[int, int, int]) -> None:
        if 0 <= x < w and 0 <= y < h:
            idx = (y * w + x) * 3
            pixels[idx : idx + 3] = bytes(col)

    left, right, top, bottom = 70, w - 40, 40, h - 60
    for x in range(left, right + 1):
        set_px(x, bottom, axis_col)
    for y in range(top, bottom + 1):
        set_px(left, y, axis_col)

    max_val = max(values) if values else 1.0
    n = len(values)
    slot_w = (right - left) // max(n, 1)
    bar_w = int(slot_w * 0.55)

    for i, val in enumerate(values):
        bh = int(((val / max_val) if max_val > 0 else 0) * (bottom - top - 15))
        x0 = left + i * slot_w + (slot_w - bar_w) // 2
        y0 = bottom - bh
        col = bar_colors[i % len(bar_colors)]
        for y in range(y0, bottom):
            for x in range(x0, x0 + bar_w):
                set_px(x, y, col)

    raw = bytearray()
    stride = w * 3
    for y in range(h):
        raw.append(0)
        raw.extend(pixels[y * stride : (y + 1) * stride])

    def chunk(tag: bytes, data: bytes) -> bytes:
        return (
            struct.pack("!I", len(data))
            + tag
            + data
            + struct.pack("!I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    ihdr = struct.pack("!IIBBBBB", w, h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(bytes(raw))) + chunk(b"IEND", b"")
    with open(filename, "wb") as f:
        f.write(png)


def run_stage0():
    game = ConnectKGame(R=7, C=8, K=4, V=0, d=8)
    s_empty = game.initial_state()
    s_mid = game.state_from_moves([3, 4, 3, 4, 4, 3, 2, 5, 2, 5, 5, 2])

    os.makedirs("results", exist_ok=True)
    rows = []

    for label, state in [("bos_tahta", s_empty), ("yari_dolu", s_mid)]:
        for n in range(1, 6):
            t0 = time.perf_counter()
            nodes = perft(game, state, n)
            elapsed = round(time.perf_counter() - t0, 5)
            rows.append([label, n, nodes, elapsed])

    with open("results/stage0_perft.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["konum", "n", "dugum_sayisi", "sure_sn"])
        writer.writerows(rows)


def run_stage1():
    game = ConnectKGame(R=7, C=8, K=4, V=0, d=8)
    agent = MinimaxAgent(game)

    positions = [
        ("K1_bos", game.initial_state()),
        ("K2_merkez", game.state_from_moves([3, 4, 3, 4])),
        ("K3_orta", game.state_from_moves([3, 4, 3, 4, 4, 3, 2, 5])),
        ("K4_tehdit", game.state_from_moves([3, 0, 4, 0, 5, 0])),
        ("K5_yaridolu", game.state_from_moves([3, 4, 3, 4, 4, 3, 2, 5, 2, 5, 5, 2])),
    ]

    os.makedirs("results", exist_ok=True)
    rows = []

    for label, state in positions:
        for depth in (2, 4, 6):
            move, val = agent.choose_move(state, depth=depth)
            nodes = agent.last_stats.nodes
            b_eff = round(nodes ** (1.0 / depth), 4)
            elapsed = round(agent.last_stats.elapsed, 5)
            rows.append([label, depth, move, val, nodes, b_eff, elapsed])

    with open("results/stage1_minimax.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["konum", "derinlik", "hamle", "deger", "dugum_sayisi", "b_etkin", "sure_sn"])
        writer.writerows(rows)


def generate_random_positions(game: ConnectKGame, count: int = 50, seed: int = 8):
    rng = random.Random(seed)
    positions = []
    seen_boards = set()
    while len(positions) < count:
        state = game.initial_state()
        plies = rng.randint(6, 16)
        ok = True
        for _ in range(plies):
            actions = game.actions(state)
            if not actions or game.is_terminal(state):
                ok = False
                break
            state = game.result(state, rng.choice(actions))
        if ok and not game.is_terminal(state) and state.board not in seen_boards:
            seen_boards.add(state.board)
            positions.append(state)
    return positions


def run_stage2():
    game = ConnectKGame(R=7, C=8, K=4, V=0, d=8)
    positions = generate_random_positions(game, count=50, seed=8)
    depth = 6

    mm_agent = MinimaxAgent(game)
    ab_agents = {
        "a_siralamasiz": AlphaBetaAgent(game, ordering="none"),
        "b_merkez": AlphaBetaAgent(game, ordering="center"),
        "c_taktiksel": AlphaBetaAgent(game, ordering="tactical"),
    }

    os.makedirs("results", exist_ok=True)
    per_pos_rows = []
    totals = {k: {"nodes": 0, "time": 0.0, "ord_time": 0.0} for k in ["minimax", *ab_agents.keys()]}

    print("50 rastgele konum üzerinde Derinlik 6 doğrulama ve karşılaştırma başlıyor...")
    for idx, state in enumerate(positions, start=1):
        _, val_mm = mm_agent.choose_move(state, depth=depth)
        n_mm = mm_agent.last_stats.nodes
        t_mm = mm_agent.last_stats.elapsed
        totals["minimax"]["nodes"] += n_mm
        totals["minimax"]["time"] += t_mm

        row = [idx, val_mm, n_mm, round(t_mm, 5)]
        for key, agent in ab_agents.items():
            _, val_ab = agent.choose_move(state, depth=depth)
            assert val_ab == val_mm, f"HATA! Konum {idx}: {key} ({val_ab}) != Minimax ({val_mm})"
            assert agent.last_stats.nodes <= n_mm, f"HATA! Konum {idx}: {key} daha fazla düğüm gezdi!"

            totals[key]["nodes"] += agent.last_stats.nodes
            totals[key]["time"] += agent.last_stats.elapsed
            totals[key]["ord_time"] += agent.last_stats.ordering_time
            row.extend([agent.last_stats.nodes, round(agent.last_stats.elapsed, 5)])

        per_pos_rows.append(row)
        if idx % 10 == 0:
            print(f"  {idx}/50 konum doğrulandı ve ölçüldü...")

    with open("results/stage2_per_position.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "konum_no", "kok_deger",
            "mm_dugum", "mm_sure",
            "a_siralamasiz_dugum", "a_siralamasiz_sure",
            "b_merkez_dugum", "b_merkez_sure",
            "c_taktiksel_dugum", "c_taktiksel_sure",
        ])
        writer.writerows(per_pos_rows)

    summary_rows = []
    mm_avg_nodes = totals["minimax"]["nodes"] / 50.0
    print(f"\n{'Yöntem':<18} | {'Ort. Düğüm':<12} | {'Kazanç (%)':<11} | {'Ort. Süre (sn)':<14} | {'Sıralama Maliyeti (sn)':<22}")
    print("-" * 86)

    for key in ["minimax", "a_siralamasiz", "b_merkez", "c_taktiksel"]:
        avg_n = round(totals[key]["nodes"] / 50.0, 2)
        avg_t = round(totals[key]["time"] / 50.0, 5)
        avg_ord = round(totals[key]["ord_time"] / 50.0, 5)
        saving_pct = round((1.0 - (avg_n / mm_avg_nodes)) * 100.0, 2)
        summary_rows.append([key, avg_n, saving_pct, avg_t, avg_ord])
        print(f"{key:<18} | {avg_n:<12} | %{saving_pct:<10} | {avg_t:<14} | {avg_ord:<22}")

    with open("results/stage2_summary.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["yontem", "ortalama_dugum", "budama_kazanci_yuzde", "ortalama_sure_sn", "siralama_maliyeti_sn"])
        writer.writerows(summary_rows)

    _save_bar_chart_png(
        "results/stage2_nodes.png",
        [r[0] for r in summary_rows],
        [r[1] for r in summary_rows],
    )
    print("\nAşama 2 tabloları ve results/stage2_nodes.png grafiği başarıyla kaydedildi.")


if __name__ == "__main__":
    run_stage2()