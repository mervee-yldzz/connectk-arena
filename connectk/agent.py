import argparse
import os
import sys

# Hangi klasörden çalıştırılırsa çalıştırılsın connectk paketini bulmasını sağlar
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from connectk.game import ConnectKGame
from connectk.evaluate import Evaluator
from connectk.search import TimedAlphaBetaAgent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Connect-K Arena Turnuva Ajanı")
    parser.add_argument("--R", type=int, default=7, help="Satır sayısı")
    parser.add_argument("--C", type=int, default=8, help="Sütun sayısı")
    parser.add_argument("--K", type=int, default=4, help="Kazanma taş sayısı")
    parser.add_argument("--V", type=int, default=0, help="Varyasyon (0..3)")
    parser.add_argument("--seed", type=int, default=8, help="Rastgelelik tohumu (d)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    game = ConnectKGame(R=args.R, C=args.C, K=args.K, V=args.V, d=args.seed)
    evaluator = Evaluator(game)
    agent = TimedAlphaBetaAgent(
        game=game,
        eval_fn=evaluator,
        use_tt=True,
        threat_extension=True,
        seed=args.seed,
    )

    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue

        if line == "QUIT":
            break

        if line.startswith("MOVES"):
            parts = line.split()[1:]
            moves = [int(x) for x in parts]
            try:
                state = game.state_from_moves(moves)
                legal = game.actions(state)
                if not legal:
                    print("0", flush=True)
                    continue

                move, val = agent.choose_move(state, time_limit=1.0)
                if move not in legal:
                    move = legal[0]

                print(
                    f"[DEBUG] hamle={move} deger={val:.3f} derinlik={agent.last_stats.depth_reached} "
                    f"dugum={agent.last_stats.nodes} sure={agent.last_stats.elapsed:.3f}s",
                    file=sys.stderr,
                )
                print(move, flush=True)
            except Exception as exc:
                print(f"[HATA] {exc}", file=sys.stderr)
                fallback = game.actions(game.initial_state())
                print(fallback[0] if fallback else 0, flush=True)


if __name__ == "__main__":
    main()