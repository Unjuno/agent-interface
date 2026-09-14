"""Golden desktop v3 with a doctor that covers the actual GUI import closure."""
from __future__ import annotations

import importlib
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
RESEARCH = ROOT / "research" / "live_control"
for path in (HERE, RESEARCH):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import golden_desktop_demo_v2 as previous


BASE_DOCTOR = previous.base.doctor
ADDITIONAL_RUNTIME_MODULES = ("openpyxl", "et_xmlfile")


def doctor() -> dict:
    result = BASE_DOCTOR()
    checks = list(result["checks"])
    for name in ADDITIONAL_RUNTIME_MODULES:
        try:
            module = importlib.import_module(name)
        except Exception as error:
            checks.append({"name": "python:" + name, "passed": False,
                           "detail": f"{type(error).__name__}: {error}"})
        else:
            checks.append({"name": "python:" + name, "passed": True,
                           "detail": getattr(module, "__version__", "version unavailable")})
    return {
        **result,
        "schema": "agent_interface_golden_doctor_v2",
        "passed": all(row["passed"] for row in checks),
        "checks": checks,
    }


def run_live(out: Path, seed: int, **kwargs) -> dict:
    previous.base.doctor = doctor
    return previous.run_live(out, seed, **kwargs)


def main() -> int:
    previous.base.doctor = doctor
    previous.base.run_live = run_live
    return previous.base.main()


if __name__ == "__main__":
    raise SystemExit(main())
