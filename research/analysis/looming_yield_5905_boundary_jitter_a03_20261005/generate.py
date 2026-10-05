#!/usr/bin/env python3
"""Fresh-seed wrapper over the frozen A02 geometry/fixture generator."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
BASE_PACKAGE = ROOT.parent / "looming_yield_5905_boundary_jitter_a02_20261005"
spec = importlib.util.spec_from_file_location("boundary_jitter_a02_generator", BASE_PACKAGE / "generate.py")
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
base.ROOT = ROOT
base.SEED = 20261011
SEED = base.SEED
TIMES = base.TIMES
CONTACT = base.CONTACT


def generate():
    return base.generate()


def write():
    return base.write()


if __name__ == "__main__":
    data = write()
    print({"seed": SEED, "cases": len(data["manifest"]["cases"])})
