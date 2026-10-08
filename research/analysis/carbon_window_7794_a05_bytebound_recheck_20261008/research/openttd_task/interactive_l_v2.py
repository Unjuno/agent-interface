"""Run the seed-991004 changed-geometry L fixture through the v1 task protocol."""
from pathlib import Path

import interactive_l_v1 as protocol


HERE = Path(__file__).resolve().parent
protocol.SAVE = HERE / "results/l-geometry-02/baseline.sav"
protocol.SAVE_SHA = "88faddae21bd6a24406165941ed02c6746eda8b2cb744747790af6eba786371f"


if __name__ == "__main__":
    protocol.main()
