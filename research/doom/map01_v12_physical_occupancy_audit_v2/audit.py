"""Supplement R1's frozen audit with admission, step, source and terminal binding.

This reads evidence only. It never starts a session or grants input authority.
It is not a replacement for launch uniqueness, environment or cleanup gates.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
R1 = HERE.parent / "map01_v12_physical_occupancy_live_r1_v1"
spec = importlib.util.spec_from_file_location("map01_r1_frozen_bridge", R1 / "r0_bridge_snapshot.py")
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)
STEPS = [{"op": "hold", "keys": ["a", "d"], "duration_ms": 250}, {"op": "observe"}]


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha_bytes(value):
    return hashlib.sha256(value).hexdigest()


def program_sha(steps):
    return sha_bytes(json.dumps(steps, sort_keys=True, separators=(",", ":"),
                                ensure_ascii=False, allow_nan=False).encode("utf-8"))


def expected_sources():
    """Read canonical Git bytes, so Windows CRLF cannot change expected identity."""
    freeze = read(R1 / "SOURCE_FREEZE.json")
    result = {}
    for path, frozen_blob in freeze["current_main_inputs"].items():
        actual = subprocess.check_output(["git", "rev-parse", f"HEAD:{path}"],
                                         cwd=REPO, text=True).strip()
        if actual != frozen_blob:
            raise ValueError(f"R1 source drift: {path}")
        if path.endswith("fixture.json"):
            continue  # Fixture/engine provenance is a separate gate.
        raw = subprocess.check_output(["git", "cat-file", "blob", frozen_blob], cwd=REPO)
        result[path.removeprefix("research/")] = sha_bytes(raw)
    wrapper = "map01_v12_transition_owner.py"
    blob = freeze["frozen_source_blobs"][wrapper]
    actual = subprocess.check_output(["git", "rev-parse", f"HEAD:{R1.relative_to(REPO).as_posix()}/{wrapper}"],
                                     cwd=REPO, text=True).strip()
    if actual != blob:
        raise ValueError("R1 wrapper source drift")
    result[f"external/{wrapper}"] = sha_bytes(subprocess.check_output(
        ["git", "cat-file", "blob", blob], cwd=REPO))
    result.update({f"external/{name}": digest
                   for name, digest in freeze["retained_v12_sha256"].items()})
    return result


def _verify(rows, sources, program_id, required_sources):
    errors = []

    def require(ok, label):
        if not ok:
            errors.append(label)

    def exactly_one(candidates, label):
        require(len(candidates) == 1, label)
        return candidates[0] if len(candidates) == 1 else {}

    def ns(value):
        return type(value) is int and value >= 0

    require(type(program_id) is str and bool(program_id.strip()), "program_id")
    require(bool(required_sources), "empty_source_expectations")
    require(type(sources) is dict and all(sources.get(name) == digest
            for name, digest in required_sources.items()), "required_source_identity")
    submit_row = exactly_one([r for r in rows if r.get("event") == "command" and
                              r.get("command", {}).get("op") == "submit"], "one_submit")
    submit = submit_row.get("command", {})
    accepted = exactly_one([r for r in rows if r.get("event") == "accepted"], "one_acceptance")
    terminal = exactly_one([r for r in rows if r.get("event") == "terminal"], "one_terminal")
    require(submit.get("id") == accepted.get("id") == terminal.get("id") == program_id,
            "program_identity")
    require(submit.get("steps") == STEPS and
            program_sha(submit.get("steps")) == program_sha(STEPS), "fixed_r1_program")
    require(type(accepted.get("steps")) is int and accepted.get("steps") == len(STEPS) and
            accepted.get("program_sha256") == program_sha(STEPS), "accepted_program_attestation")
    token = accepted.get("intent_token")
    require(type(token) is str and bool(token.strip()), "accepted_intent_token")
    accepted_ns, terminal_ns = accepted.get("accepted_ns"), terminal.get("terminal_ns")
    require(ns(accepted_ns) and ns(terminal_ns) and accepted_ns <= terminal_ns,
            "accepted_terminal_order")
    deadline = accepted.get("valid_until_ns")
    require(ns(deadline) and deadline == submit.get("valid_until_ns") and
            ns(accepted_ns) and accepted_ns < deadline, "admitted_deadline")
    require(terminal.get("status") == "completed" and type(terminal.get("steps_completed")) is int and
            terminal.get("steps_completed") == len(STEPS), "completed_two_step_terminal")
    release = terminal.get("release", {})
    require(release.get("verified") is True and release.get("keys_down") == [] and
            release.get("buttons_down") == [], "terminal_verified_empty")
    require(ns(release.get("verified_ns")) and ns(terminal_ns) and
            ns(accepted_ns) and accepted_ns <= release["verified_ns"] <= terminal_ns,
            "terminal_release_order")
    held = exactly_one([r for r in rows if r.get("event") == "keys_held"], "one_hold")
    require(held.get("id") == program_id and type(held.get("step")) is int and held.get("step") == 0 and
            held.get("keys") == ["a", "d"], "held_step_identity")
    completions = [r for r in rows if r.get("event") == "step_completed"]
    require(len(completions) == 2 and all(r.get("id") == program_id and type(r.get("step")) is int
            for r in completions) and sorted(r["step"] for r in completions) == [0, 1],
            "completed_step_identity")
    hold_completion = next((r.get("completed_ns") for r in completions
                            if r.get("id") == program_id and r.get("step") == 0), None)
    observe_completion = next((r.get("completed_ns") for r in completions
                               if r.get("id") == program_id and r.get("step") == 1), None)
    require(all(ns(t) for t in (hold_completion, observe_completion, release.get("verified_ns"))) and
            hold_completion <= observe_completion <= release["verified_ns"], "final_step_release_order")
    down_rows = [r for r in rows if r.get("event") == "input_admission"]
    releases = [r for r in rows if r.get("event") == "input_release_transition"]
    require(len(down_rows) == 2 and sorted(str(r.get("key")) for r in down_rows) == ["a", "d"],
            "exact_down_keys")
    require(len(releases) == 2, "two_release_rows")
    pairs = {}
    for up_row in releases:
        key = up_row.get("key")
        down_matches = [r for r in down_rows if r.get("key") == key]
        down_row = exactly_one(down_matches, f"one_down_for_{key}")
        down = down_row.get("physical_key_measurement", {}).get("adapter_edge", {})
        up = up_row.get("physical_key_measurement", {}).get("adapter_edge", {})
        require(up_row.get("release_batch_identifier") == program_id and
                up_row.get("release_batch_step") == 0, f"release_step_{key}")
        require(type(token) is str and all(r.get("intent_token") == token
                for r in (down_row, up_row, down, up)), f"accepted_lease_{key}")
        require(ns(deadline) and up_row.get("valid_until_ns") == deadline and
                ns(up_row.get("release_call_returned_ns")) and
                up_row["release_call_returned_ns"] <= deadline, f"release_deadline_{key}")
        require(down.get("key") == up.get("key") == key, f"physical_key_{key}")
        div, uiv = down.get("interval"), up.get("interval")
        if (type(div) is list and type(uiv) is list and len(div) == len(uiv) == 2
                and all(ns(t) for t in div + uiv) and ns(accepted_ns)
                and ns(terminal_ns) and ns(hold_completion) and ns(held.get("input_ack_ns"))):
            require(accepted_ns <= div[0] <= div[1] <= held["input_ack_ns"] <=
                    uiv[0] <= uiv[1] <= hold_completion <= terminal_ns,
                    f"admitted_step_edge_order_{key}")
        else:
            require(False, f"edge_timestamps_{key}")
        if type(key) is str:
            pairs[key] = [down, up]
    bound = bridge.bind_batch(releases, pairs, bridge.EXPECTED_SOURCE)
    require(bound["status"] == "BOUND_MAP01_PHYSICAL_BATCH", "r0_physical_batch")
    require(bound.get("grants_input_authority") is False, "no_authority")
    return _result(program_id, errors, bound["status"])


def _result(program_id, errors, bridge_status="NOT_EVALUATED"):
    return {"schema": "map01-physical-admission-supplement-v2", "passed": not errors,
            "errors": errors, "program_id": program_id, "bridge_status": bridge_status,
            "grants_input_authority": False,
            "full_r1_gate_eligible": False,
            "scope": "source/accepted-program/step/lease/terminal linkage supplement only",
            "separate_gates": ["launch uniqueness and lease", "fixture/engine identity",
                               "physical precision", "external process cleanup",
                               "task-useful effect and recovery efficacy"]}


def verify(rows, sources, program_id, required_sources):
    """Malformed evidence is a refusal, never a partial or full gate success."""
    if type(rows) is not list or any(type(row) is not dict for row in rows):
        return _result(program_id, ["event_rows_shape"])
    if type(required_sources) is not dict or any(
            type(name) is not str or not name or type(digest) is not str or len(digest) != 64 or
            any(c not in "0123456789abcdef" for c in digest)
            for name, digest in required_sources.items()):
        return _result(program_id, ["source_expectations_shape"])
    try:
        return _verify(rows, sources, program_id, required_sources)
    except (KeyError, TypeError, ValueError, AttributeError):
        return _result(program_id, ["malformed_event_evidence"])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--program-id", required=True)
    args = parser.parse_args()
    rows = [json.loads(line) for line in (args.runtime / "events.jsonl").read_text(
        encoding="utf-8").splitlines() if line.strip()]
    value = verify(rows, read(args.runtime / "sources.json"), args.program_id, expected_sources())
    print(json.dumps(value, indent=2, sort_keys=True))
    return 0 if value["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
