"""Verify retained pins, invariants, package hashes, and an optional fresh replay."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RUN_OUTPUTS = (
    "normal.stdout.txt", "normal.stderr.txt", "normal.exit.txt",
    "optimized.stdout.txt", "optimized.stderr.txt", "optimized.exit.txt",
    "RESULT.json",
)


def select_results_dir(raw_path):
    if raw_path is None:
        return HERE
    results_dir = Path(raw_path).expanduser().resolve()
    try:
        results_dir.relative_to(HERE.resolve())
    except ValueError:
        pass
    else:
        raise ValueError("replay results must be outside the retained evidence package")
    if not results_dir.is_dir():
        raise ValueError(f"replay results directory does not exist: {results_dir}")
    return results_dir


def verify(results_dir):
    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    result = json.loads((results_dir / "RESULT.json").read_text(encoding="utf-8"))
    expected = freeze["sources"]
    assert len(expected) == 7
    actual = {
        path: subprocess.check_output(
            ["git", "-C", str(REPO), "rev-parse", f"{freeze['main_commit']}:{path}"],
            text=True,
        ).strip()
        for path in expected
    }
    assert actual == expected
    assert result["main_commit"] == freeze["main_commit"]
    assert result["source_blobs"] == expected
    assert result["disposition"] == "PASS_EXACT_PRODUCER_TO_EXECUTOR_RECOVERY_COMPOSITION"
    assert result["producer_pair"] == {
        "sequence": 2, "typed_before_full": True,
        "capture_binding_hash_match": True, "health": 86, "ammo": 12,
    }
    assert result["stale_sequence_1"] == {
        "reason": "latest observation sequence required before input",
        "compiled_once": True, "accepted_events": 0,
        "backend_validation_calls": 0, "worker_starts": 0,
        "retried_after_rejection": False,
    }
    fresh = result["fresh_sequence_2"]
    assert fresh["planner_turn_count"] == 2
    assert fresh["used_exact_producer_image"] and fresh["used_paired_typed_hud"]
    assert fresh["accepted_events"] == 1 and fresh["backend_validation_calls"] == 1
    assert fresh["worker_started_inertly"] is True and fresh["physical_input"] is False
    assert result["second_drift_sequence_3"] == {
        "reason": "latest observation sequence required before input",
        "accepted_events": 0, "backend_validation_calls": 0, "worker_starts": 0,
    }
    assert result["controls"] == {
        "non_stale_rejection": "refused", "no_fresh_observation": "refused",
        "missing_typed_event": "refused", "binding_mismatch": "refused",
        "frame_hash_mismatch": "refused",
    }
    normal = (results_dir / "normal.stdout.txt").read_bytes()
    optimized = (results_dir / "optimized.stdout.txt").read_bytes()
    assert normal == optimized
    assert json.loads(normal.decode("utf-8")) == result
    for label in ("normal", "optimized"):
        assert (results_dir / f"{label}.exit.txt").read_text(encoding="ascii").strip() == "0"
        assert not (results_dir / f"{label}.stderr.txt").read_bytes()
    for line in (HERE / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        digest, name = line.split("  ", 1)
        assert hashlib.sha256((HERE / name).read_bytes()).hexdigest() == digest, name
    if results_dir != HERE:
        assert {p.name for p in results_dir.iterdir()} == set(RUN_OUTPUTS)
        for name in RUN_OUTPUTS:
            assert (results_dir / name).read_bytes() == (HERE / name).read_bytes(), name


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir",
                        help="verify a fresh replay directory; omit for the retained package only")
    args = parser.parse_args(argv)
    try:
        results_dir = HERE if args.results_dir is None else select_results_dir(args.results_dir)
        verify(results_dir)
    except (OSError, ValueError, AssertionError, subprocess.CalledProcessError,
            json.JSONDecodeError) as exc:
        parser.error(f"verification failed: {exc}")
    print("PASS: source pins, recovery/admission invariants, retained package hashes, and replay outputs")


if __name__ == "__main__":
    main()

