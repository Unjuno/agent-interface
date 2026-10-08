"""Reproduce this retained-data package without overwriting it."""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, required=True,
                        help="new directory on a volume with sufficient free space")
    args = parser.parse_args()
    out = args.out_dir.resolve()
    out.mkdir(parents=True, exist_ok=False)

    from analyze import reconstruct
    from audit import audit
    from guard_replay import compute as compute_guard
    from action_gate_replay import compute as compute_action_gate

    result = reconstruct(ROOT)
    write_json(out / "RESULT.replay.json", result)
    audited = audit(ROOT, out / "RESULT.replay.json")
    write_json(out / "AUDIT.replay.json", audited)
    guard = compute_guard()
    write_json(out / "GUARD_REPLAY.replay.json", guard)
    action_gate = compute_action_gate()
    write_json(out / "ACTION_GATE_REPLAY.replay.json", action_gate)

    retained = {
        "RESULT.json": json.loads((ROOT / "RESULT.json").read_text(encoding="utf-8")),
        "AUDIT.json": json.loads((ROOT / "AUDIT.json").read_text(encoding="utf-8")),
        "GUARD_REPLAY.json": json.loads((ROOT / "GUARD_REPLAY.json").read_text(encoding="utf-8")),
        "ACTION_GATE_REPLAY.json": json.loads((ROOT / "ACTION_GATE_REPLAY.json").read_text(encoding="utf-8")),
    }
    produced = {
        "RESULT.json": result,
        "AUDIT.json": audited,
        "GUARD_REPLAY.json": guard,
        "ACTION_GATE_REPLAY.json": action_gate,
    }
    if produced != retained:
        raise ValueError("fresh reconstruction differs from a retained candidate or audit")

    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    commands = [
        [sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-v"],
        [sys.executable, "-O", "-B", "-m", "unittest", "discover", "-s", "tests", "-v"],
    ]
    for label, command in zip(("normal", "optimized"), commands):
        run = subprocess.run(command, cwd=ROOT, env=env, text=True,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (out / f"tests.{label}.stdout.txt").write_text(run.stdout, encoding="utf-8")
        (out / f"tests.{label}.stderr.txt").write_text(run.stderr, encoding="utf-8")
        (out / f"tests.{label}.exit.txt").write_text(str(run.returncode) + "\n", encoding="utf-8")
        if run.returncode != 0:
            raise RuntimeError(f"{label} unit tests failed; inspect {out}")

    summary = {
        "verified": True,
        "fresh_result_matches_retained": True,
        "fresh_audit_matches_retained": True,
        "fresh_guard_replay_matches_retained": True,
        "fresh_action_gate_replay_matches_retained": True,
        "normal_tests": "PASS",
        "optimized_tests": "PASS",
        "output_directory": str(out),
    }
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
