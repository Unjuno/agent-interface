"""One-seed paired formal builder; host orchestrator supplies explicit bindings."""
import os
from pathlib import Path

from support_probe import build, load_upstream

SEEDS = (7865101, 7865201, 7865301, 7865401, 7865501,
         7865601, 7865701, 7865801, 7865901, 7866001)


def main():
    if "NEEDLE_SEED" not in os.environ or "NEEDLE_OUTPUT" not in os.environ:
        raise SystemExit("STOP_MISSING_NEEDLE_ENV")
    seed = int(os.environ["NEEDLE_SEED"])
    out = Path(os.environ["NEEDLE_OUTPUT"])
    if seed not in SEEDS or not out.is_dir() or any(out.iterdir()):
        raise SystemExit("STOP_FORMAL_SEED_OR_OUTPUT")
    upstream = load_upstream("/src/source/runner.py")
    build(upstream, seed, out)


if __name__ == "__main__":
    main()
