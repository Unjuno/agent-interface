"""Retained no-input packet checker; no subprocess, Tk, X11 or WSLc calls."""
import contextlib
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
from audit_epoch import main as audit_main


ROOT = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def manifest_errors(root, lines):
    root = Path(root).resolve()
    errors, seen = [], set()
    for line in lines:
        expected, separator, name = line.partition("  ")
        path = PurePosixPath(name)
        if (not separator or not re.fullmatch(r"[a-f0-9]{64}", expected) or
                not name or path.is_absolute() or ".." in path.parts or
                "\\" in name or ":" in name or name == "SHA256SUMS"):
            errors.append("unsafe_manifest_path")
            continue
        target = (root / name).resolve()
        if root not in target.parents:
            errors.append("escaping_manifest_path")
            continue
        if name in seen:
            errors.append("duplicate_manifest_path")
        seen.add(name)
        try:
            if sha(target) != expected:
                errors.append("manifest_hash:" + name)
        except OSError:
            errors.append("manifest_missing:" + name)
    actual = {p.relative_to(root).as_posix() for p in root.rglob("*")
              if p.is_file() and p.relative_to(root).as_posix() != "SHA256SUMS"
              and "__pycache__" not in p.parts}
    if seen != actual:
        errors.append("incomplete_manifest")
    return errors


def scope_errors(run):
    expected = {"disposition": "PASS_CONSTRUCTION_CUSTODY_NO_INPUT_ONLY",
                "container_invocations": 1, "apps": 8, "retries": 0,
                "input_events": 0, "first_character_formal_invocations": 0}
    return ["run_scope:" + key for key, value in expected.items() if run.get(key) != value]


def main():
    errors = manifest_errors(ROOT, (ROOT / "SHA256SUMS").read_text().splitlines())
    run = json.loads((ROOT / "RUN.json").read_bytes())
    errors.extend(scope_errors(run))
    for name, expected in run["sha256"].items():
        if sha(ROOT / name) != expected:
            errors.append("run_hash:" + name)
    capture = io.StringIO()
    with contextlib.redirect_stdout(capture):
        code = audit_main(ROOT / "results/construction01-data", ROOT / "FREEZE_CONSTRUCTION.json",
                          ROOT / "results/construction01-launch")
    rebuilt = json.loads(capture.getvalue())
    retained = json.loads((ROOT / "results/retained-audit01-launch/stdout.bin").read_bytes())
    if code or rebuilt != retained:
        errors.append("retained_audit_reconstruction")
    receipt_dir = ROOT / "results/retained-audit01-launch"
    receipt = json.loads((receipt_dir / "receipt.json").read_bytes())
    attempt = json.loads((receipt_dir / "attempt.json").read_bytes())
    if receipt["exit_code"] != 0 or receipt["launch_error"] is not None:
        errors.append("retained_audit_exit")
    if receipt["argv"] != attempt["argv"] or receipt["started_utc"] != attempt["started_utc"]:
        errors.append("retained_audit_attempt")
    for name, expected in receipt["output_sha256"].items():
        if sha(receipt_dir / name) != expected:
            errors.append("retained_audit_stream:" + name)
    result = {"status": "FAIL_RETAINED_PACKET" if errors else "PASS_RETAINED_NO_INPUT_PACKET",
              "errors": errors, "rows": rebuilt["rows"],
              "legacy_duplicate_rows": rebuilt["legacy_duplicate_rows"],
              "fixed_single_epoch_rows": rebuilt["fixed_single_epoch_rows"],
              "scope": rebuilt["scope"], "formal_commands_executed": 0}
    print(json.dumps(result, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
