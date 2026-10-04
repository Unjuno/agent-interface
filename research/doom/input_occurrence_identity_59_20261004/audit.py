"""Independent source/hash and exhaustive detection-bracket audit."""
import hashlib
import itertools
import json
import subprocess
from pathlib import Path

from attribution import attribute_positive_events, normalize_releases

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
manifest = json.loads((BASE / "SOURCE_MANIFEST.json").read_text(encoding="utf-8"))

for path, pinned in manifest["base_sources"].items():
    data = subprocess.run(["git", "show", f"{manifest['base_commit']}:{path}"],
                          check=True, capture_output=True).stdout
    assert hashlib.sha256(data).hexdigest() == pinned["sha256"], path
    blob = subprocess.run(["git", "rev-parse", f"{manifest['base_commit']}:{path}"],
                          check=True, capture_output=True, text=True).stdout.strip()
    assert blob == pinned["blob"], path

for path, pinned in manifest["candidate_artifacts"].items():
    assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == pinned["sha256"], path

owner = (ROOT / "research/live_control/input_owner_v12.py").read_text(encoding="utf-8")
assert "input_occurrence_id" in owner
assert "key_release_intervals_ns" in owner
assert "owner_id=self.owner_id" in owner

intervals = [(start, end) for start in range(1, 5) for end in range(start + 1, 6)]
brackets = [(0, 1), (1, 2), (2, 3), (3, 4)]
checked = 0
for count in (1, 2):
    for selected in itertools.combinations_with_replacement(intervals, count):
        for lower, upper in brackets:
            samples = [
                {"schema": "independent-progress-sample-v2", "session_id": "session",
                 "sample_ns": lower},
                {"schema": "independent-progress-sample-v2", "session_id": "session",
                 "sample_ns": upper},
            ]
            events = [{
                "schema": "independent-progress-event-v2", "session_id": "session",
                "event_sequence": 1, "observed_ns": upper,
                "polarity": "positive", "useful": True,
                "controller_visible": False,
            }]
            admissions, raw_releases, bindings = [], [], []
            possible = []
            for index, (start, end) in enumerate(selected):
                program_id = f"program-{index}"
                token = f"intent-{index}"
                occurrence_id = f"owner:{index}"
                admitted_ns, ack_ns = start - 1, start
                release_start, release_end = end - 1, end
                admissions.append({
                    "session_id": "session", "id": program_id, "step": 0,
                    "keycode": index + 38, "input_occurrence_id": occurrence_id,
                    "owner_id": "owner", "intent_token": token,
                    "admitted_ns": admitted_ns, "input_ack_ns": ack_ns,
                })
                raw_releases.append({
                    "event": "input_release_transition", "session_id": "session",
                    "id": program_id, "step": 0,
                    "owner_thread_keyup_receipt": {
                        "event": "owner_explicit_keyup", "keycode": index + 38,
                        "input_occurrence_id": occurrence_id, "owner_id": "owner",
                        "intent_token": token,
                        "owner_keyrelease_started_ns": release_start,
                        "owner_sync_returned_ns": release_end,
                        "server_sync_completed": True,
                        "cancel_requested_after_sync": False,
                    },
                })
                bindings.append({
                    "session_id": "session", "program_id": program_id, "step": 0,
                    "semantic_action_sha256": f"{index + 1:064x}",
                })
                if admitted_ns <= upper and release_end >= lower:
                    possible.append((token, admitted_ns, release_end))
            tokens = {row[0] for row in possible}
            if len(tokens) > 1:
                expected = "AMBIGUOUS"
            elif len(tokens) == 1:
                _token, start, end = possible[0]
                if start == lower or end == upper:
                    expected = "UNRESOLVED"
                elif start < lower and end > upper:
                    expected = "SINGLE_POSSIBLE_INTENT_ENVELOPE"
                else:
                    expected = "UNRESOLVED"
            else:
                expected = "UNRESOLVED"
            actual = attribute_positive_events(
                samples, events, admissions, normalize_releases(raw_releases),
                bindings)[0]
            assert actual["status"] == expected, (selected, (lower, upper), actual)
            checked += 1

print(f"PASS: {len(manifest['base_sources'])} base-source pins; "
      f"{len(manifest['candidate_artifacts'])} candidate hashes; "
      f"{checked} finite detection-bracket cases match independent oracle")
