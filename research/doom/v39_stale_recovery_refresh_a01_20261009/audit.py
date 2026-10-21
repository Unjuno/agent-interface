"""Independent source, result, and raw test-output audit for A01."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
result = json.loads((ROOT / "RESULT.json").read_text(encoding="utf-8"))
failures = []

for relative, identity in freeze["source_files"].items():
    path = REPO / relative
    data = path.read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    blob = subprocess.check_output(
        ["git", "hash-object", "--", str(path)], cwd=REPO, text=True).strip()
    if sha != identity["sha256"] or blob != identity["git_blob"]:
        failures.append(f"source identity mismatch: {relative}")

test = (REPO / "research/doom/test_map01_overlap_controller_v39.py").read_text(encoding="utf-8")
refresh = (REPO / "research/doom/doom_source_refresh_v1.py").read_text(encoding="utf-8")
required_test_markers = (
    'test_stale_executor_rejection_replans_from_new_image_and_hud',
    'self.assertEqual(sent[0]["expected_sequence"], 5)',
    'self.assertEqual(source["sequence"], 6)',
    'self.assertEqual(Path(turn[1]), root / "refreshed.png")',
    'self.assertIn("health: 60", turn[0])',
    'self.assertIn("ammo: 8", turn[0])',
    'self.assertEqual(refused.exception.receipt["reason"], "refresh_release_unqualified")',
    'self.assertFalse(recovered["guard"]["current_input_authority"])',
)
for marker in required_test_markers:
    if marker not in test:
        failures.append(f"missing deterministic assertion: {marker}")
for marker in ("release.get('intent_token') != accepted['intent_token']",
               "release.get('keys_down') != []", "release.get('buttons_down') != []"):
    if marker not in refresh:
        failures.append(f"source-refresh release gate missing: {marker}")

expected_runs = {
    "focused-normal": ("Ran 1 test", "OK"),
    "focused-optimized": ("Ran 1 test", "OK"),
    "controller-normal": ("Ran 16 tests", "OK"),
    "controller-optimized": ("Ran 16 tests", "OK"),
    "drain-normal": ("Ran 21 tests", "OK"),
    "drain-optimized": ("Ran 21 tests", "OK"),
}
for name, markers in expected_runs.items():
    exit_path = ROOT / "results" / f"{name}.exit"
    stderr_path = ROOT / "results" / f"{name}.stderr.txt"
    stdout_path = ROOT / "results" / f"{name}.stdout.txt"
    if not exit_path.exists() or exit_path.read_text(encoding="utf-8").strip() != "0":
        failures.append(f"nonzero/missing exit: {name}")
        continue
    output = stderr_path.read_text(encoding="utf-8") + stdout_path.read_text(encoding="utf-8")
    if not all(marker in output for marker in markers):
        failures.append(f"raw unittest transcript mismatch: {name}")

manifest = ROOT / "SHA256SUMS.txt"
audit_outputs = {"results/audit-normal.stdout.txt", "results/audit-normal.stderr.txt",
                 "results/audit-normal.exit", "results/audit-optimized.stdout.txt",
                 "results/audit-optimized.stderr.txt", "results/audit-optimized.exit"}
if manifest.exists():
    expected_hashes = {}
    for line in manifest.read_text(encoding="utf-8").splitlines():
        digest, relative = line.split("  ", 1)
        expected_hashes[relative] = digest
    actual_hashes = {
        path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in ROOT.rglob("*")
        if (path.is_file() and path != manifest and "__pycache__" not in path.parts
            and path.relative_to(ROOT).as_posix() not in audit_outputs)
    }
    if expected_hashes != actual_hashes:
        failures.append("package SHA-256 manifest mismatch")
else:
    failures.append("package SHA256SUMS.txt missing")

if result["decision"] != "PASS_SCOPED_STALE_RECOVERY_REFRESH_HANDOFF":
    failures.append("unexpected decision")
if result["observed"]["negative_mismatched_release_token"] != "refused_before_planner":
    failures.append("negative control was not retained")
if "no live game" not in result["scope"].lower():
    failures.append("scope limitation missing")

if failures:
    raise SystemExit("AUDIT_FAIL\n" + "\n".join(failures))
print(json.dumps({
    "audit": "PASS_SCOPED_STALE_RECOVERY_REFRESH_HANDOFF",
    "source_files_checked": len(freeze["source_files"]),
    "test_runs_checked": len(expected_runs),
    "negative_control": "release mismatch refuses",
    "scope": "deterministic software composition only",
}, indent=2))
