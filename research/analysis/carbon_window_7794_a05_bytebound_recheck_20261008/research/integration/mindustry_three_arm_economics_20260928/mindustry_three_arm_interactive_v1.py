"""Task-specific socket child with Issue #55 receipt revalidation enabled."""

from __future__ import annotations

import runpy
from pathlib import Path
import sys
from types import ModuleType


HERE = Path(__file__).resolve().parent
REPOSITORY = next(parent for parent in HERE.parents if (parent / ".git").exists())
LIVE = REPOSITORY / "research" / "live_control"
BENCHMARK = REPOSITORY / "research" / "benchmark_discovery"
sys.path.insert(0, str(LIVE))


def install_receipt_backend(base_module: ModuleType,
                            receipt_backend: type) -> type:
    """Swap only the task child backend, preserving the frozen child source."""
    previous = getattr(base_module, "Backend", None)
    if not isinstance(previous, type) or not isinstance(receipt_backend, type):
        raise TypeError("runtime backend classes required")
    if not issubclass(receipt_backend, previous):
        raise TypeError("receipt backend must extend the task runtime backend")
    base_module.Backend = receipt_backend
    return receipt_backend


def main() -> None:
    import cause_servo_session_v1
    from mindustry_receipt_session_v1 import Backend as ReceiptBackend

    install_receipt_backend(cause_servo_session_v1, ReceiptBackend)
    runpy.run_path(str(BENCHMARK / "mindustry_single_tile_interactive_v1.py"),
                   run_name="__main__")


if __name__ == "__main__":
    main()
