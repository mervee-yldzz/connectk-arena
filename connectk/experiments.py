import csv
import os
import random
import time
from connectk.game import ConnectKGame
from connectk.evaluate import Evaluator, DEFAULT_WEIGHTS
from connectk.search import AlphaBetaAgent, TimedAlphaBetaAgent


def run_stage3():
    game = ConnectKGame(R=7, C=8, K=4, V=0, d=8)
    weight_sets = {
        "W1_varsayilan": DEFAULT_WEIGHTS,
        "W2_agresif": (18.0, -12.0, 5.0, -2.5, 1.0, 8.0),
        "W3_savunmaci": (10.0, -22.0, 2.5, -5.5, 2.2, 6.0),
    }

    names = list(weight_sets.keys())
    wins = {a: {b: 0.0 for b in names} for a in names}
    rng = random.Random(8)

    opening_pool = []
    for _ in range(5):
        s = game.initial_state()
        for _ in range(3):
            s = game.result(s, rng.choice(game.actions(s)))
        opening_pool.append(s)

    os.makedirs("results", exist_ok=True)
    game_rows = []

    print("Aşama 3: Ağırlık vektörleri turnuvası (Derinlik 5, seed=8)...")
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            n1, n2 = names[i], names[j]
            ag1 = AlphaBetaAgent(game, eval_fn=Evaluator(game, weight_sets[n1]), ordering="tactical")
            ag2 = AlphaBetaAgent(game, eval_fn=Evaluator(game, weight_sets[n2]), ordering="tactical")

            for game_idx, start_state in enumerate(opening_pool):
                for side_swap in (False, True):
                    first_name, first_ag = (n2, ag2) if side_swap else (n1, ag1)
                    second_name, second_ag = (n1, ag1) if side_swap else (n2, ag2)

                    st = start_state
                    while not game.is_terminal(st):
                        active_ag = first_ag if st.to_move == 1 else second_ag
                        mv, _ = active_ag.choose_move(st, depth=5)
                        st = game.result(st, mv)

                    res = game.utility(st)
                    if res == 1:
                        wins[first_name][second_name] += 1.0
                        outcome = first_name
                    elif res == -1:
                        wins[second_name][first_name] += 1.0
                        outcome = second_name
                    else:
                        wins[first_name][second_name] += 0.5
                        wins[second_name][first_name] += 0.5
                        outcome = "berabere"
                    game_rows.append([first_name, second_name, game_idx + 1, outcome])

    with open("results/stage3_weights.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["agirlik_vektoru", *names, "toplam_puan"])
        for a in names:
            tot = sum(wins[a][b] for b in names if b != a)
            w.writerow([a, *[wins[a][b] if a != b else "-" for b in names], tot])

    with open("results/stage3_games.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["ilk_oyuncu_MAX", "ikinci_oyuncu_MIN", "acilis_no", "kazanan"])
        w.writerows(game_rows)

    for a in names:
        print(f"  {a:<15}: {wins[a]}")


def run_stage4():
    game = ConnectKGame(R=7, C=8, K=4, V=0, d=8)
    ev = Evaluator(game)
    os.makedirs("results", exist_ok=True)

    # 1. TT Doğruluk Kontrolü (Sabit derinlik 4'te TT Açık vs Kapalı)
    ab_ref = AlphaBetaAgent(game, eval_fn=ev, ordering="tactical")
    tt_on = TimedAlphaBetaAgent(game, eval_fn=ev, use_tt=True, threat_extension=False, seed=8)
    tt_off = TimedAlphaBetaAgent(game, eval_fn=ev, use_tt=False, threat_extension=False, seed=8)

    rng = random.Random(8)
    sample_states = []
    for _ in range(10):
        s = game.initial_state()
        for _ in range(rng.randint(4, 14)):
            s = game.result(s, rng.choice(game.actions(s)))
        sample_states.append(s)

    for s in sample_states:
        _, v_ref = ab_ref.choose_move(s, depth=4)
        _, v_tt = tt_on.search_fixed_depth(s, depth=4)
        assert abs(v_ref - v_tt) < 1e-9, "TT sabit derinlikte farklı değer verdi!"

    # 2. 10 Konumda 1.0 Saniye Limiti: TT Açık vs TT Kapalı
    per_pos_rows = []
    sum_on_d = sum_on_n = sum_off_d = sum_off_n = 0
    max_elapsed_on = 0.0

    print("\nAşama 4: 10 konumda 1.0 sn limiti (TT Açık vs TT Kapalı)...")
    for idx, s in enumerate(sample_states, start=1):
        tt_on.tt.clear()
        mv_on, _ = tt_on.choose_move(s, time_limit=1.0)
        d_on, n_on, t_on, hits = (
            tt_on.last_stats.depth_reached,
            tt_on.last_stats.nodes,
            round(tt_on.last_stats.elapsed, 4),
            tt_on.last_stats.tt_hits,
        )
        max_elapsed_on = max(max_elapsed_on, tt_on.last_stats.elapsed)

        mv_off, _ = tt_off.choose_move(s, time_limit=1.0)
        d_off, n_off, t_off = (
            tt_off.last_stats.depth_reached,
            tt_off.last_stats.nodes,
            round(tt_off.last_stats.elapsed, 4),
        )

        sum_on_d += d_on
        sum_on_n += n_on
        sum_off_d += d_off
        sum_off_n += n_off
        per_pos_rows.append([idx, mv_on, d_on, n_on, hits, t_on, mv_off, d_off, n_off, t_off])

    with open("results/stage4_depth_per_position.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["konum", "tt_acik_hamle", "tt_acik_derinlik", "tt_acik_dugum", "tt_isabet", "tt_acik_sure", "tt_kapali_hamle", "tt_kapali_derinlik", "tt_kapali_dugum", "tt_kapali_sure"])
        w.writerows(per_pos_rows)

    with open("results/stage4_depth_summary.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["mod", "ort_derinlik", "ort_dugum", "maks_sure_sn"])
        w.writerow(["TT_Acik", round(sum_on_d / 10, 2), round(sum_on_n / 10, 1), round(max_elapsed_on, 4)])
        w.writerow(["TT_Kapali", round(sum_off_d / 10, 2), round(sum_off_n / 10, 1), "-"])

    print(f"  TT Açık  -> Ort. Derinlik: {sum_on_d/10:.2f}, Ort. Düğüm: {sum_on_n/10:.1f}, Maks Süre: {max_elapsed_on:.4f} sn")
    print(f"  TT Kapalı-> Ort. Derinlik: {sum_off_d/10:.2f}, Ort. Düğüm: {sum_off_n/10:.1f}")

    # 3. Ufuk Etkisi Karşılaştırması: Tehdit Uzatması Kapalı (d=2) vs Açık (d=2+1) vs Derin (d=4)
    # MAX'in hemen yapabileceği pasif hamle sonrası MIN'in 2 hamlede çifte tehdit / kazanma kurduğu konum
    horizon_state = game.state_from_moves([3, 1, 4, 2, 0, 1, 5, 2])
    no_ext = TimedAlphaBetaAgent(game, eval_fn=ev, use_tt=False, threat_extension=False, seed=8)
    with_ext = TimedAlphaBetaAgent(game, eval_fn=ev, use_tt=False, threat_extension=True, seed=8)

    m_d2, v_d2 = no_ext.search_fixed_depth(horizon_state, depth=2)
    m_ext, v_ext = with_ext.search_fixed_depth(horizon_state, depth=2)
    m_d4, v_d4 = no_ext.search_fixed_depth(horizon_state, depth=4)

    with open("results/stage4_horizon.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["ayar", "secilen_hamle", "deger", "dugum_sayisi"])
        w.writerow(["Derinlik_2_Uzatma_Kapali", m_d2, round(v_d2, 4), no_ext.last_stats.nodes])
        w.writerow(["Derinlik_2_Tehdit_Uzatmasi_Acik", m_ext, round(v_ext, 4), with_ext.last_stats.nodes])
        w.writerow(["Derinlik_4_Referans", m_d4, round(v_d4, 4), no_ext.last_stats.nodes])

    print(f"  Ufuk Etkisi -> d=2 hamle: {m_d2} ({v_d2:.3f}), d=2+uzatma hamle: {m_ext} ({v_ext:.3f}), d=4 hamle: {m_d4} ({v_d4:.3f})")


if __name__ == "__main__":
    run_stage3()
    run_stage4()