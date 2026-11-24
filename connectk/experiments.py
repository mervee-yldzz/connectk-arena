import csv
import os
import time
from connectk.game import ConnectKGame, perft
from connectk.search import MinimaxAgent


def run_stage0():
    game = ConnectKGame(R=7, C=8, K=4, V=0, d=8)
    s_empty = game.initial_state()
    s_mid = game.state_from_moves([3, 4, 3, 4, 4, 3, 2, 5, 2, 5, 5, 2])

    os.makedirs("results", exist_ok=True)
    rows = []

    print(f"{'Konum':<12} | {'Derinlik (n)':<12} | {'Düğüm Sayısı':<14} | {'Süre (sn)':<10}")
    print("-" * 58)

    for label, state in [("bos_tahta", s_empty), ("yari_dolu", s_mid)]:
        for n in range(1, 6):
            t0 = time.perf_counter()
            nodes = perft(game, state, n)
            elapsed = round(time.perf_counter() - t0, 5)
            rows.append([label, n, nodes, elapsed])
            print(f"{label:<12} | {n:<12} | {nodes:<14} | {elapsed:<10}")

    with open("results/stage0_perft.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["konum", "n", "dugum_sayisi", "sure_sn"])
        writer.writerows(rows)

    print("\nAşama 0 tablosu results/stage0_perft.csv dosyasına kaydedildi.")


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

    print(f"\n{'Konum':<12} | {'Derinlik':<8} | {'Hamle':<6} | {'Değer':<6} | {'Düğüm':<10} | {'b_etkin':<8} | {'Süre (sn)':<9}")
    print("-" * 74)

    for label, state in positions:
        for depth in (2, 4, 6):
            move, val = agent.choose_move(state, depth=depth)
            nodes = agent.last_stats.nodes
            b_eff = round(nodes ** (1.0 / depth), 4)
            elapsed = round(agent.last_stats.elapsed, 5)
            rows.append([label, depth, move, val, nodes, b_eff, elapsed])
            print(f"{label:<12} | {depth:<8} | {move:<6} | {val:<6} | {nodes:<10} | {b_eff:<8} | {elapsed:<9}")

    with open("results/stage1_minimax.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["konum", "derinlik", "hamle", "deger", "dugum_sayisi", "b_etkin", "sure_sn"])
        writer.writerows(rows)

    print("\nAşama 1 tablosu results/stage1_minimax.csv dosyasına kaydedildi.")


if __name__ == "__main__":
    run_stage1()