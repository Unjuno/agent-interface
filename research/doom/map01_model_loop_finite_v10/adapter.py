"""Fresh MAP01 successor changing only the inter-segment observe lease horizon."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE_PATH = HERE.parent / "map01_model_loop_finite_v7" / "adapter.py"
spec = importlib.util.spec_from_file_location("map01_finite_v7_adapter", BASE_PATH)
v7 = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(v7)
base = v7.base

OLD = '"valid_until_ns":clock_ns+5_000_000_000'
NEW = '"valid_until_ns":clock_ns+15_000_000_000'

def main() -> None:
    source = base.SOURCE.read_text(encoding="utf-8")
    if source.count(OLD) != 1:
        raise RuntimeError(f"expected exactly one refresh-lease anchor, found {source.count(OLD)}")
    base.REPLACEMENTS = tuple(base.REPLACEMENTS) + ((OLD, NEW),)
    module = base.load_controller()
    if module._freshstart_effective_source.count(NEW) != 1:
        raise RuntimeError("effective source does not contain exactly one 15-second refresh lease")
    if module._freshstart_effective_source.count(OLD):
        raise RuntimeError("effective source still contains the 5-second refresh lease")
    if "--prepare-only" in sys.argv:
        target = Path(sys.argv[sys.argv.index("--prepare-only") + 1]).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(module._freshstart_effective_source, encoding="utf-8")
        print(f"effective_controller_sha256={module._freshstart_sha256}")
        print(f"effective_controller_path={target}")
        return
    module.main()

if __name__ == "__main__":
    main()
