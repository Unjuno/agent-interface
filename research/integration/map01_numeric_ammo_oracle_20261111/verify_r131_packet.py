"""Read-only source/asset/packet hash check for the R131 candidate."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess


CHECKOUT = Path(__file__).resolve().parents[3]
PACKET = (CHECKOUT.parent.parent / "private-packets" /
    "map01_native_windows_delayed_cancel_20261111_r131_resolver_encoding_receipt")


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify() -> dict:
    conditions_path = PACKET / "conditions.json"
    conditions = json.loads(conditions_path.read_text(encoding="utf-8"))
    source = conditions["source"]
    head = subprocess.check_output(["git", "rev-parse", "HEAD"],
        cwd=CHECKOUT, text=True).strip()
    if head != source["main_commit"]:
        raise ValueError("checkout HEAD changed after packet freeze")
    checks = {}
    for group, base in (("runtime_sha256", CHECKOUT),
                        ("research_sha256", CHECKOUT),
                        ("packet_sha256", PACKET)):
        rows = source[group]
        for rel, expected in rows.items():
            actual = sha256(base / rel)
            checks[f"{group}:{rel}"] = actual == expected
            if actual != expected:
                raise ValueError(f"pinned {group} hash mismatch: {rel}")
    assets = conditions["assets"]
    for path_key, hash_key in (("gzdoom_path", "gzdoom_sha256"),
            ("freedoom_iwad_path", "freedoom_iwad_sha256"),
            ("seed_config_path", "seed_config_sha256")):
        actual = sha256(Path(assets[path_key]))
        checks[f"asset:{path_key}"] = actual == assets[hash_key]
        if actual != assets[hash_key]:
            raise ValueError(f"pinned asset hash mismatch: {path_key}")
    for label, expected in conditions["mode0_oracle_templates_sha256"].items():
        path = PACKET / "mode0_templates" / f"ammo_{label}_template.png"
        actual = sha256(path)
        checks[f"template:{label}"] = actual == expected
        if actual != expected:
            raise ValueError(f"pinned HUD template hash mismatch: {label}")
    if conditions.get("attempt_id") != "map01-native-gzdoom-expiry-scan-code-demo-r131-20261111":
        raise ValueError("unexpected attempt ID")
    if conditions.get("isolation", {}).get("preserved_unknown_processes", [{}])[0].get("pid") != 55376:
        raise ValueError("protected GZDoom process baseline changed")
    return {"status": "all-pinned-hashes-match",
        "attempt_id": conditions["attempt_id"],
        "head": head,
        "runtime_count": len(source["runtime_sha256"]),
        "research_count": len(source["research_sha256"]),
        "packet_count": len(source["packet_sha256"]),
        "asset_and_template_count": 5,
        "conditions_sha256": sha256(conditions_path),
        "checks": checks,
        "live_target_preflight": "not_performed",
        "input_sent": False}


if __name__ == "__main__":
    print(json.dumps(verify(), sort_keys=True, indent=2))
