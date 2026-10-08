"""Refuse to run the archived candidate when its one-shot outputs exist."""
from pathlib import Path


ROOT = Path(__file__).resolve().parent
FROZEN_OUTPUTS = (
    "RAW-30.json",
    "AUDIT.json",
    "RUN.json",
    "PRE-RUN.json",
    "SHA256SUMS.txt",
)
existing = [name for name in FROZEN_OUTPUTS if (ROOT / name).exists()]
if existing:
    raise SystemExit(
        "STOP: refusing historical rerun because frozen outputs exist: "
        + ", ".join(existing)
        + ". No files were changed. Use verify_preserved_hold_bound_30.py."
    )
raise SystemExit(
    "STOP: no candidate execution is implemented here. Create a separately "
    "frozen successor with a new run identity and output directory."
)
