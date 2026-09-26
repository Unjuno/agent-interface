"""Allocation-v2 entrypoint over the frozen v1 paired trainer."""
from pathlib import Path
import sys

ALLOCATION = "needle-lora-rank1-online-skill-v2"
SEEDS = (74111, 74222, 74333)

dependency = Path("/src/v1")
if not dependency.is_dir():
    dependency = Path(__file__).resolve().parent.parent / "needle_lora_rank1_online_skill_v1"
sys.path.insert(0, str(dependency))
import runner as frozen_runner

frozen_runner.ALLOCATION = ALLOCATION
frozen_runner.SEEDS = SEEDS


if __name__ == "__main__":
    frozen_runner.main()
