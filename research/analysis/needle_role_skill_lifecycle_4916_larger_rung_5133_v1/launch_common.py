from __future__ import annotations

import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE_ROOT = ROOT.parent / "needle_role_skill_lifecycle_4916_larger_rung_v1"
ALLOCATION = "needle-role-skill-lifecycle-4916-larger-rung-20260928-03"


def load_runner(module_name: str):
    sys.path.insert(0, str(SOURCE_ROOT))
    module = importlib.import_module(module_name)
    module.ROOT = ROOT
    module.ALLOCATION = ALLOCATION
    return module


def launch(module_name: str) -> int:
    return load_runner(module_name).main()
