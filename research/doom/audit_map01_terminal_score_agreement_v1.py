"""Audit exact agreement between v13 final independent scorer sample and v12 score."""
from __future__ import annotations
import argparse, json
from pathlib import Path

FIELDS = ("map_exit", "episode_finished", "player_dead", "death_count", "kill_count")
SAMPLE_SCHEMA = "independent-progress-sample-v2"


def _jsonl(path: Path):
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def audit(root: Path) -> dict:
    root = Path(root)
    failures = []
    score_path = root / "score.json"
    samples_path = root / "scorer-samples.jsonl"
    if not score_path.is_file():
        failures.append("score.json missing")
        score = None
    else:
        score = json.loads(score_path.read_text(encoding="utf-8"))
    if not samples_path.is_file():
        failures.append("scorer-samples.jsonl missing")
        rows = []
    else:
        rows = _jsonl(samples_path)

    direct = [r for r in rows if r.get("direct_final_sample") is True]
    if len(direct) != 1:
        failures.append(f"expected exactly one direct_final_sample, got {len(direct)}")
    if direct and rows and direct[0] is not rows[-1]:
        failures.append("direct_final_sample is not final scorer record")

    compared = {}
    if score is not None and len(direct) == 1:
        payload = direct[0].get("payload")
        if not isinstance(payload, dict):
            failures.append("direct_final_sample payload missing")
        elif payload.get("schema") != SAMPLE_SCHEMA:
            failures.append("direct_final_sample schema mismatch")
        else:
            for field in FIELDS:
                if field not in score or field not in payload:
                    failures.append(f"terminal field missing: {field}")
                    continue
                s, p = score[field], payload[field]
                equal = type(s) is type(p) and s == p
                compared[field] = {"score": s, "scorer": p, "strict_equal": equal}
                if not equal:
                    failures.append(f"terminal field disagreement: {field}")

    return {
        "schema": "map01-terminal-score-agreement-audit-v1",
        "pass": not failures,
        "failures": failures,
        "direct_final_sample_count": len(direct),
        "terminal_fields": compared,
        "decision": "PASS terminal score agreement" if not failures else "FAIL terminal score agreement",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root", type=Path)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    result = audit(args.root)
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    print(text, end="")
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    raise SystemExit(0 if result["pass"] else 1)

if __name__ == "__main__":
    main()
