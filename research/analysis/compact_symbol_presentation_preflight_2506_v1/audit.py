"""Independent compact-symbol semantic-equivalence preflight."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

DICT = {"goal": "G", "phase": "P", "status": "S", "risk": "R", "unknown": "?"}
ALLOWED = {"goal", "phase", "status", "risk", "unknown"}


def encode(facts: dict[str, str]) -> str:
    if set(facts) - ALLOWED:
        raise ValueError("unknown field")
    return "|".join(f"{DICT[k]}={facts[k]}" for k in sorted(facts))


def decode(symbols: str) -> dict[str, str]:
    out = {}
    for item in symbols.split("|"):
        key, sep, value = item.partition("=")
        if not sep or key not in set(DICT.values()) or not value:
            raise ValueError("invalid symbol")
        name = next(name for name, symbol in DICT.items() if symbol == key)
        if name in out:
            raise ValueError("duplicate symbol")
        out[name] = value
    return out


def oracle(facts: dict[str, str]) -> str:
    # Separate canonical oracle: does not call encode/decode.
    return "|".join(f"{DICT[k]}={facts[k]}" for k in sorted(facts))


def main() -> None:
    cases = [
        ("ordinary", {"goal": "explore", "phase": "audit", "status": "ready"}),
        ("all-known", {"goal": "G1", "phase": "P2", "status": "hold", "risk": "low"}),
        ("unknown-explicit", {"goal": "?", "unknown": "provider"}),
        ("ordering", {"status": "ready", "goal": "explore", "phase": "audit"}),
        ("empty-rejected", {}),
    ]
    rows = []
    passed = 0
    for name, facts in cases:
        try:
            compact = encode(facts)
            decoded = decode(compact)
            ok = decoded == facts and compact == oracle(facts)
        except ValueError:
            ok = name == "empty-rejected"
            compact = "REJECT"
        rows.append({"case": name, "pass": ok, "compact": compact})
        passed += ok

    rejects = {
        "tamper": lambda: decode("G=explore|P=audit|S=ready|X=bad"),
        "duplicate": lambda: decode("G=explore|G=again"),
        "dictionary-mismatch": lambda: decode("Q=explore"),
        "extra-field": lambda: encode({"goal": "x", "evaluator_only": "leak"}),
    }
    for name, fn in rejects.items():
        try:
            fn()
            ok = False
        except ValueError:
            ok = True
        rows.append({"case": name, "pass": ok, "expected": "reject"})
        passed += ok

    canonical = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()
    result = {
        "schema": "compact-symbol-preflight-2506-v1",
        "status": "PASS_COMPACT_SEMANTIC_EQUIVALENCE_PREFLIGHT" if passed == len(rows) else "FAIL",
        "scope": "representation_integrity_only",
        "model_run": False,
        "authority_grants": 0,
        "cases": len(rows),
        "passed": passed,
        "independent_oracle": True,
        "rows": rows,
        "result_sha256": hashlib.sha256(canonical).hexdigest(),
    }
    out = Path(__file__).with_name("RESULT.json")
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
