#!/usr/bin/env python3
"""Exercise independent raw-auditor rejection on copied evidence only."""
import argparse
import json
from pathlib import Path
import shutil
import tempfile

from audit import validate


def rewrite_rows(path: Path, mutate) -> None:
    rows = [json.loads(line) for line in (path / "raw.jsonl").read_text(encoding="utf-8").splitlines()]
    mutate(rows)
    (path / "raw.jsonl").write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8")


def controls(evidence: Path) -> dict:
    mutations = {
        "raw_hash_changed": lambda path: rewrite_rows(path, lambda rows: rows[0].update(candidate_sha256="0" * 64)),
        "row_removed": lambda path: rewrite_rows(path, lambda rows: rows.pop()),
        "row_duplicated": lambda path: rewrite_rows(path, lambda rows: rows.append(dict(rows[0]))),
        "case_id_changed": lambda path: rewrite_rows(path, lambda rows: rows[0]["case"].update(case_id="tampered")),
        "candidate_byte_changed": lambda path: rewrite_rows(path, lambda rows: rows[0].update(candidate_bytes_b64="AA==")),
        "native_byte_changed": lambda path: rewrite_rows(path, lambda rows: rows[0].update(native_bytes_b64="AA==")),
        "source_pixel_changed": lambda path: rewrite_rows(path, lambda rows: rows[0]["source_pixels"].__setitem__(0, rows[0]["source_pixels"][0] ^ 1)),
        "geometry_changed": lambda path: rewrite_rows(path, lambda rows: rows[0]["geometry"].update(width=rows[0]["geometry"]["width"] + 1)),
        "fixture_exit_changed": lambda path: rewrite_rows(path, lambda rows: rows[0].update(fixture_exit=17)),
        "tcp_enabled": lambda path: rewrite_rows(path, lambda rows: rows[0].update(tcp_listening=True)),
        "cleanup_removed": lambda path: rewrite_rows(path, lambda rows: rows[0].update(cleanup_complete=False)),
        "summary_count_changed": lambda path: (path / "summary.json").write_text(json.dumps({**json.loads((path / "summary.json").read_text(encoding="utf-8")), "failed": 1}), encoding="utf-8"),
    }
    results = []
    with tempfile.TemporaryDirectory(prefix="x11-string8-controls-") as temp:
        temp_root = Path(temp)
        for name, mutate in mutations.items():
            copied = temp_root / name
            shutil.copytree(evidence, copied)
            mutate(copied)
            audit = validate(copied)
            results.append({"name": name, "rejected": audit["status"] == "FAIL_AUDIT", "errors": audit["errors"]})
    return {"controls": results, "rejected": sum(item["rejected"] for item in results), "total": len(results), "status": "PASS_CONTROLS" if all(item["rejected"] for item in results) else "FAIL_CONTROLS"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = controls(args.evidence)
    encoded = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if args.out:
        args.out.write_text(encoded, encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS_CONTROLS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
