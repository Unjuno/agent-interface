"""Independent source/hash and exhaustive temporal-state audit."""
import hashlib
import itertools
import json
import subprocess
from pathlib import Path

from attribution import attribute_progress_events, normalize_releases

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
manifest = json.loads((BASE / "SOURCE_MANIFEST.json").read_text(encoding="utf-8"))

for path, pinned in manifest["base_sources"].items():
    data = subprocess.run(
        ["git", "show", f"{manifest['base_commit']}:{path}"],
        check=True, capture_output=True).stdout
    assert hashlib.sha256(data).hexdigest() == pinned["sha256"], path
    blob = subprocess.run(
        ["git", "rev-parse", f"{manifest['base_commit']}:{path}"],
        check=True, capture_output=True, text=True).stdout.strip()
    assert blob == pinned["blob"], path

for path, pinned in manifest["candidate_artifacts"].items():
    assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == pinned["sha256"], path

owner = (ROOT / "research/live_control/input_owner_v12.py").read_text(encoding="utf-8")
assert "input_occurrence_id" in owner
assert "key_release_intervals_ns" in owner
assert "owner_id=self.owner_id" in owner

intervals = [(start, end, end + 1)
             for start in range(3) for end in range(start + 1, 4)]
checked = 0
for count in (1, 2):
    for selected in itertools.combinations_with_replacement(intervals, count):
        for observed in range(6):
            admissions = []
            releases = []
            bindings = []
            expected_active = []
            expected_boundary = []
            for index, (ack, release_start, release_end) in enumerate(selected):
                program_id = f"program-{index}"
                occurrence_id = f"owner:{index}"
                admissions.append({
                    "event": "input_admission", "id": program_id, "step": 0,
                    "keycode": index + 38, "input_occurrence_id": occurrence_id,
                    "owner_id": "owner", "intent_token": f"intent-{index}",
                    "input_ack_ns": ack,
                })
                releases.append({
                    "event": "input_release_transition", "id": program_id,
                    "owner_thread_keyup_receipt": {
                        "event": "owner_explicit_keyup", "keycode": index + 38,
                        "input_occurrence_id": occurrence_id, "owner_id": "owner",
                        "intent_token": f"intent-{index}",
                        "owner_keyrelease_started_ns": release_start,
                        "owner_sync_returned_ns": release_end,
                        "server_sync_completed": True,
                        "cancel_requested_after_sync": False,
                    },
                })
                bindings.append({"program_id": program_id, "step": 0,
                                 "semantic_action_sha256": f"{index + 1:064x}"})
                if ack <= observed < release_start:
                    expected_active.append(occurrence_id)
                elif release_start <= observed < release_end:
                    expected_boundary.append(occurrence_id)
            event = {"schema": "independent-progress-event-v2",
                     "event_sequence": 1, "observed_ns": observed,
                     "kind": "KILL_COUNT_INCREASE",
                     "controller_visible": False}
            actual = attribute_progress_events(
                [event], admissions, normalize_releases(releases), bindings)[0]
            if expected_boundary:
                expected = "unresolved_release_boundary"
            elif len(expected_active) == 1:
                expected = "unique_temporal_occurrence"
            elif len(expected_active) > 1:
                expected = "ambiguous_multiple_active_occurrences"
            else:
                expected = "unresolved_no_active_occurrence"
            assert actual["status"] == expected, (selected, observed, actual)
            checked += 1

print(f"PASS: {len(manifest['base_sources'])} current-main pins; "
      f"{len(manifest['candidate_artifacts'])} candidate hashes; "
      f"{checked} finite scorer/admission/release cases match independent oracle")
