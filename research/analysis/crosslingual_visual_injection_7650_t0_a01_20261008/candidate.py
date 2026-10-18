#!/usr/bin/env python3
"""Create a synthetic 2x2 bookkeeping fixture; strings are NOT translations."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "RAW.json"
LANGS = ("en", "tr")
CLASSES = ("malicious", "benign", "distractor")
GEOMETRY = {"panel": [0, 0, 800, 600], "target": [40, 80, 360, 140], "visible": True}


def rows() -> list[dict]:
    result = []
    for family in range(1, 41):
        for task_lang in LANGS:
            for embedded_lang in LANGS:
                for kind in CLASSES:
                    for variant in range(2):
                        uid = f"F{family:02d}-{task_lang}-{embedded_lang}-{kind}-V{variant}"
                        result.append({
                            "uid": uid,
                            "family": f"F{family:02d}",
                            "task_lang": task_lang,
                            "embedded_lang": embedded_lang,
                            "class": kind,
                            "variant": variant,
                            "task_source": "trusted_user",
                            "embedded_source": "untrusted_ui" if kind != "distractor" else "none",
                            "task_text_status": "PLACEHOLDER_NOT_LINGUISTIC_STIMULUS",
                            "embedded_text_status": "PLACEHOLDER_NOT_LINGUISTIC_STIMULUS",
                            "semantic_equivalence": "UNKNOWN_NOT_ADJUDICATED",
                            "geometry": GEOMETRY,
                        })
    return result


def main() -> None:
    data = {"schema": "7650-machine-gate-spike-v1", "rows": rows()}
    raw = (json.dumps(data, sort_keys=True, separators=(",", ":")) + "\n").encode()
    OUT.write_bytes(raw)
    print(json.dumps({"rows": len(data["rows"]), "sha256": hashlib.sha256(raw).hexdigest(), "path": "RAW.json"}, sort_keys=True))


if __name__ == "__main__":
    main()
