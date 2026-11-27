"""Recheck the retained R281 packet without launching the runner or GUI."""
from __future__ import annotations
import hashlib
import json
import pathlib
import posixpath
import subprocess
import tarfile

ROOT = pathlib.Path(__file__).resolve().parent
MAIN = "381a21ace42891c2cd1e9cff3e231bec763ec2ba"

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def read_json(data: bytes):
    return json.loads(data.decode("utf-8-sig"))

# Verify every transferred original packet file against its original manifest.
original_entries = 0
for line in (ROOT / "SHA256SUMS.txt").read_text(encoding="utf-8-sig").splitlines():
    if not line.strip():
        continue
    expected, name = line.split(None, 1)
    name = name.strip().lstrip("*")
    path = ROOT / pathlib.PurePosixPath(name)
    if not path.is_file() or sha(path.read_bytes()) != expected.lower():
        raise SystemExit(f"original custody mismatch: {name}")
    original_entries += 1

# Verify the additive repository packet manifest when it has been generated.
packet_manifest_path = ROOT / "SHA256SUMS.json"
packet_entries = 0
if packet_manifest_path.is_file():
    packet_manifest = read_json(packet_manifest_path.read_bytes())
    for row in packet_manifest.get("files", []):
        name = row["path"]
        path = ROOT / name
        if (not path.is_file() or path.stat().st_size != row["size_bytes"] or
                sha(path.read_bytes()) != row["sha256"]):
            raise SystemExit(f"repository packet manifest mismatch: {name}")
        packet_entries += 1

archive_path = ROOT / "R281-raw.tar.gz"
archive_hash = sha(archive_path.read_bytes())
expected_archive = "248662bc4109662568b2a8ca09a0efe98c97b78d727474a3ccee9be3eca9738e"
if archive_hash != expected_archive:
    raise SystemExit("raw archive digest mismatch")

with tarfile.open(archive_path, "r:gz") as archive:
    members = archive.getmembers()
    for member in members:
        normalized = posixpath.normpath(member.name)
        if normalized.startswith("../") or normalized in ("..", ".") or normalized.startswith("/"):
            raise SystemExit(f"unsafe archive member: {member.name}")
        if member.issym() or member.islnk():
            raise SystemExit(f"archive link refused: {member.name}")
    def member_bytes(name: str) -> bytes:
        stream = archive.extractfile(name)
        if stream is None:
            raise SystemExit(f"missing archive member: {name}")
        return stream.read()
    source_verify = read_json(member_bytes("SOURCE_VERIFY.json"))
    if source_verify.get("all_match") is not True or source_verify.get("count") != 41:
        raise SystemExit("source snapshot verification record is invalid")
    source_matches = 0
    for row in source_verify["files"]:
        result = subprocess.run(
            ["git", "rev-parse", f"{MAIN}:{row['path']}"],
            cwd=ROOT.parents[2], capture_output=True, text=True, check=False)
        actual = result.stdout.strip() if result.returncode == 0 else None
        if actual != row["expected"]:
            raise SystemExit(f"current-main source blob differs: {row['path']}")
        source_matches += 1
    events = [read_json(line) for line in member_bytes("trial/events.jsonl").splitlines() if line.strip()]
    owner = read_json(member_bytes("trial/owner-events.json"))
    score = read_json(member_bytes("trial/score.json"))
    driver = [read_json(line) for line in member_bytes("driver.jsonl").splitlines() if line.strip()]

# Recompute the discriminating event facts from raw streams.
typed = [row for row in events if row.get("event") == "typed_observation"]
def signal(row, name):
    return row.get("signals", {}).get(name, {}).get("value")
by_id = {}
for row in events:
    if row.get("event") == "typed_observation":
        by_id.setdefault(row.get("id"), []).append(row)
terminals = {row.get("id"): row for row in events if row.get("event") == "terminal"}
started = [row for row in events if row.get("event") == "step_started"]
inputs = [row for row in events if row.get("event") == "input_admission"]
expiry_releases = [row for row in owner if row.get("reason") == "expired"]
if len(events) != 38 or len(typed) != 7:
    raise SystemExit("unexpected event counts")
if (signal(by_id["initial"][0], "ammo"), signal(by_id["initial"][0], "health")) != (50, 100):
    raise SystemExit("baseline mismatch")
old = terminals.get("R281-one-shot", {})
if old.get("status") != "expired" or old.get("steps_completed") != 0 or old.get("interruption", {}).get("record", {}).get("reason") != "expired":
    raise SystemExit("expired terminal mismatch")
if any(r.get("id") == "R281-one-shot" and r.get("step") == 1 for r in started):
    raise SystemExit("stale delayed step started")
if len(expiry_releases) != 1:
    raise SystemExit("expected one expiry owner release")
release = expiry_releases[0]
if (release.get("verified") is not True or release.get("buttons_down") != [] or
        release.get("keys_down") != [] or release.get("keys_unknown") != [] or
        release.get("key_state_errors") != []):
    raise SystemExit("expiry release was not verified neutral")
delay_ns = release["verified_ns"] - release["valid_until_ns"]
recovery = terminals.get("R281-recovery", {})
effect = terminals.get("R281-live-effect", {})
if recovery.get("status") != "completed" or by_id["R281-recovery"][0].get("sequence") != 4:
    raise SystemExit("fresh recovery observation mismatch")
space_inputs = [(i, r) for i, r in enumerate(events)
                if r.get("event") == "input_admission" and r.get("key") == "space"]
space_owner = None
if len(space_inputs) == 1:
    prior_steps = [r for r in events[:space_inputs[0][0]]
                   if r.get("event") == "step_started"]
    space_owner = prior_steps[-1].get("id") if prior_steps else None
if (len(space_inputs) != 1 or space_owner != "R281-live-effect" or
        effect.get("status") != "completed" or by_id["R281-live-effect"][-1].get("sequence") != 7):
    raise SystemExit("separate task action mismatch")
last = by_id["R281-live-effect"][-1]
if (signal(last, "ammo"), signal(last, "health")) != (49, 100):
    raise SystemExit("task effect observation mismatch")
if effect.get("release", {}).get("verified") is not True:
    raise SystemExit("task action final release mismatch")
if any(r.get("event") == "input_released" for r in events):
    raise SystemExit("standalone input_released unexpectedly present")
score_row = next((r for r in events if r.get("event") == "post_control_score"), {})
driver_end = next((r for r in driver if r.get("event") == "driver_end"), {})
process = driver_end.get("disposition", {}).get("process", {})
if score_row.get("map_exit") is not False or score_row.get("player_dead") is not False or process.get("returncode") != 0:
    raise SystemExit("post-control limits/process status mismatch")

result = {
    "schema": "wslc-map01-r281-independent-recheck-v1",
    "main_sha": MAIN,
    "original_manifest_entries_verified": original_entries,
    "repository_packet_entries_verified": packet_entries,
    "raw_archive_sha256": archive_hash,
    "tar_members": len(members),
    "unsafe_paths_or_links": 0,
    "source_git_blobs_matched": source_matches,
    "event_count": len(events),
    "typed_observations": len(typed),
    "expiry_release_verified_neutral": True,
    "expiry_release_delay_ns": delay_ns,
    "stale_delayed_step_started": False,
    "fresh_recovery_sequence": 4,
    "separate_attack_count": 1,
    "post_attack_sequence": 7,
    "ammo": {"before": 50, "after": 49},
    "standalone_input_released_event_count": 0,
    "map_exit": score_row.get("map_exit"),
    "player_dead": score_row.get("player_dead"),
    "runner_returncode": process.get("returncode"),
    "disposition": "ONE_BOUNDED_EFFECT_VERIFIED; NOT_MAP_COMPLETION_OR_EFFICIENCY_OR_RELIABILITY"
}
(ROOT / "AUDIT_RECHECK.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, sort_keys=True))


