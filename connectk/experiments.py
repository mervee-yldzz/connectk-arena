import csv
import os
import time
from connectk.game import ConnectKGame, perft


def run_stage0():
    # Öğrenci numarası sonu 08 -> (R=7, C=8, K=4, V=0, d=8)
    game = ConnectKGame(R=7, C=8, K=4, V=0, d=8)

    # 1. Konum: Tamamen boş tahta
    s_empty = game.initial_state()

    # 2. Konum: Henüz kimsenin kazanmadığı 12 hamlelik yarı dolu orta oyun konumu
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

    print("\nTablo otomatik olarak results/stage0_perft.csv dosyasina kaydedildi.")


if __name__ == "__main__":
    run_stage0()