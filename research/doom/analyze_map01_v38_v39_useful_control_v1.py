"""Conservative useful-control reconstruction from retained MAP01 v38/v39 logs.

This analysis intentionally reports bounds. The retained runtime records X11-
synchronized key-down acknowledgements but does not emit a timestamp for every
normal key-up. For a normally completed hold, the frozen backend ordering gives
a release bracket: the penultimate exact observation is captured while the hold
is still active, while the final exact observation is captured only after the
key-up calls have synchronized. Interrupted holds retain a verified-empty upper
bound but no equally strong positive-duration lower bound.
"""
import hashlib
import json
from collections import defaultdict
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE / "results"
OUT = ROOT / "map01-v38-v39-useful-control-posthoc-v1"
RUNS = ("map01-v38-integrated-threat-live-01",
        "map01-v39-coast-liveness-live-01")


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def read_events(path):
    return [json.loads(line) for line in
            Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def ms(ns):
    return round(ns / 1e6, 3)


def union_ns(intervals):
    """Length of union of half-open [start,end) monotonic-ns intervals."""
    rows = sorted((a, b) for a, b in intervals if a < b)
    if not rows:
        return 0
    total = 0
    left, right = rows[0]
    for a, b in rows[1:]:
        if a <= right:
            right = max(right, b)
        else:
            total += right - left
            left, right = a, b
    return total + right - left


def clip(interval, start, end):
    a, b = max(interval[0], start), min(interval[1], end)
    return (a, b) if a < b else None


def single(rows, description):
    if len(rows) != 1:
        raise AssertionError(f"{description}: expected 1 row, got {len(rows)}")
    return rows[0]


def reconstruct_hold_bounds(events):
    commands = {}
    held = {}
    observations = defaultdict(list)
    completed = {}
    releases = {}
    terminals = {}

    for row in events:
        kind = row.get("event")
        if kind == "command":
            command = row.get("command", {})
            if command.get("op") == "submit":
                identifier = command["id"]
                if identifier in commands:
                    raise AssertionError(f"duplicate submit id: {identifier}")
                commands[identifier] = command
        elif kind == "keys_held":
            key = (row["id"], row["step"])
            if key in held:
                raise AssertionError(f"duplicate keys_held: {key}")
            held[key] = row
        elif kind == "observation":
            observations[(row["id"], row["step"])].append(row)
        elif kind == "step_completed":
            key = (row["id"], row["step"])
            if key in completed:
                raise AssertionError(f"duplicate step_completed: {key}")
            completed[key] = row
        elif kind == "input_released":
            identifier = row["id"]
            if identifier in releases:
                raise AssertionError(f"duplicate input_released: {identifier}")
            releases[identifier] = row
        elif kind == "terminal":
            identifier = row["id"]
            if identifier in terminals:
                raise AssertionError(f"duplicate terminal: {identifier}")
            terminals[identifier] = row

    result = []
    for identifier, command in commands.items():
        for index, step in enumerate(command["steps"]):
            if step.get("op") != "hold":
                continue
            key = (identifier, index)
            receipt = held.get(key)
            if receipt is None:
                result.append({
                    "id": identifier,
                    "step": index,
                    "keys": step.get("keys"),
                    "duration_ms": step.get("duration_ms"),
                    "status": "NO_KEYS_HELD_RECEIPT",
                })
                continue

            start = receipt["input_ack_ns"]
            exact = sorted(observations.get(key, []),
                           key=lambda row: row["capture_ns"])
            done = completed.get(key)

            if done is not None:
                before_done = [row for row in exact
                               if row["capture_ns"] <= done["completed_ns"]]
                if len(before_done) < 2:
                    raise AssertionError(
                        f"completed hold lacks held/post-release observation pair: {key}")
                release_lower = before_done[-2]["capture_ns"]
                release_upper = before_done[-1]["capture_ns"]
                if not (start <= release_lower <= release_upper <=
                        done["completed_ns"]):
                    raise AssertionError(f"invalid completed-hold ordering: {key}")
                basis = "NORMAL_COMPLETION_SOURCE_ORDER"
            else:
                release = releases.get(identifier)
                terminal = terminals.get(identifier)
                if release is not None:
                    owner = release.get("owner_release", {})
                    if owner.get("verified") is not True:
                        raise AssertionError(
                            f"unverified early release for {identifier}")
                    if owner.get("keys_down") != [] or owner.get("buttons_down") != []:
                        raise AssertionError(
                            f"nonempty early release for {identifier}")
                    release_upper = owner["verified_ns"]
                elif terminal is not None:
                    owner = terminal.get("release", {})
                    if owner.get("verified") is not True:
                        raise AssertionError(
                            f"unverified terminal release for {identifier}")
                    if owner.get("keys_down") != [] or owner.get("buttons_down") != []:
                        raise AssertionError(
                            f"nonempty terminal release for {identifier}")
                    release_upper = owner["verified_ns"]
                else:
                    release_upper = None

                # Independent owner release can occur immediately after the
                # cancellation bit is set, before cancel_requested is emitted.
                # Do not use cancel_requested as a strict release lower bound.
                release_lower = start
                basis = ("INTERRUPTED_VERIFIED_EMPTY_UPPER_ONLY"
                         if release_upper is not None
                         else "INTERRUPTED_RELEASE_UPPER_UNAVAILABLE")

            if release_upper is not None and release_upper < start:
                raise AssertionError(f"release precedes held acknowledgement: {key}")
            result.append({
                "id": identifier,
                "step": index,
                "keys": sorted(step["keys"]),
                "duration_ms": step["duration_ms"],
                "status": "BOUNDED" if release_upper is not None else "UPPER_UNAVAILABLE",
                "held_start_ack_ns": start,
                "release_lower_ns": release_lower,
                "release_upper_ns": release_upper,
                "release_bracket_ms": (
                    ms(release_upper - release_lower)
                    if release_upper is not None else None),
                "basis": basis,
            })
    return result


def accepted_motor_envelope(events, command_by_id, identifier, start, end):
    accepted = single([row for row in events
                       if row.get("event") == "accepted" and row.get("id") == identifier],
                      f"accepted {identifier}")
    terminal = single([row for row in events
                       if row.get("event") == "terminal" and row.get("id") == identifier],
                      f"terminal {identifier}")
    command = command_by_id[identifier]
    if not any(step.get("op") == "hold" and step.get("keys")
               for step in command["steps"]):
        return None
    return clip((accepted["accepted_ns"], terminal["terminal_ns"]), start, end)


def analyze_run(name):
    root = ROOT / name
    report_path = root / "report.json"
    event_path = root / "runtime" / "events.jsonl"
    sources_path = root / "runtime" / "sources.json"
    report = read_json(report_path)
    events = read_events(event_path)
    sources = read_json(sources_path)

    command_by_id = {
        row["command"]["id"]: row["command"]
        for row in events
        if row.get("event") == "command"
        and row.get("command", {}).get("op") == "submit"
    }
    holds = reconstruct_hold_bounds(events)
    holds_by_id = defaultdict(list)
    for row in holds:
        holds_by_id[row["id"]].append(row)

    decisions = []
    total_confirmed_ns = 0
    total_possible_ns = 0
    total_program_ns = 0
    for decision in report["decisions"]:
        wait_start = decision["controller_model_started_ns"]
        wait_end = decision["controller_model_ended_ns"]
        if not wait_start < wait_end:
            raise AssertionError("nonpositive model-wait interval")

        cover_ids = list(decision["cover_program_ids"])
        lower_intervals = []
        upper_intervals = []
        relevant_holds = []

        for identifier in cover_ids:
            for hold in holds_by_id.get(identifier, []):
                if hold["status"] == "NO_KEYS_HELD_RECEIPT":
                    continue
                lower = clip((hold["held_start_ack_ns"], hold["release_lower_ns"]),
                             wait_start, wait_end)
                if lower:
                    lower_intervals.append(lower)
                if hold["release_upper_ns"] is not None:
                    upper = clip((hold["held_start_ack_ns"], hold["release_upper_ns"]),
                                 wait_start, wait_end)
                    if upper:
                        upper_intervals.append(upper)
                relevant_holds.append({
                    "id": hold["id"], "step": hold["step"], "basis": hold["basis"],
                    "release_bracket_ms": hold.get("release_bracket_ms"),
                })

        confirmed = union_ns(lower_intervals)
        possible = union_ns(upper_intervals)
        wait_ns = wait_end - wait_start
        if not 0 <= confirmed <= possible <= wait_ns:
            raise AssertionError("invalid held-input coverage bounds")

        program_intervals = []
        for identifier in cover_ids:
            interval = accepted_motor_envelope(
                events, command_by_id, identifier, wait_start, wait_end)
            if interval:
                program_intervals.append(interval)
        motor_program = union_ns(program_intervals)
        if motor_program > wait_ns:
            raise AssertionError("program-envelope coverage exceeds wait")

        total_confirmed_ns += confirmed
        total_possible_ns += possible
        total_program_ns += motor_program

        decisions.append({
            "iteration": decision["iteration"],
            "planner_status": decision["planner_turn_status"],
            "final_admission": decision["final_action_admission"]["status"],
            "model_wait_ms": ms(wait_ns),
            "motor_capable_program_envelope_ms": ms(motor_program),
            "x11_acknowledged_held_coverage_lower_ms": ms(confirmed),
            "x11_acknowledged_held_coverage_upper_ms": ms(possible),
            "no_held_input_lower_ms": ms(wait_ns - possible),
            "no_held_input_upper_ms": ms(wait_ns - confirmed),
            "cover_ids": cover_ids,
            "bounded_hold_receipts": relevant_holds,
        })

    total_wait = sum(
        decision["controller_model_ended_ns"] -
        decision["controller_model_started_ns"]
        for decision in report["decisions"])
    score = report["score"]
    return {
        "run": name,
        "source_sha256": {
            "report.json": sha256(report_path),
            "runtime/events.jsonl": sha256(event_path),
            "runtime/sources.json": sha256(sources_path),
        },
        "retained_runtime_source_manifest": sources,
        "decisions": decisions,
        "totals": {
            "model_wait_ms": ms(total_wait),
            "motor_capable_program_envelope_ms": ms(total_program_ns),
            "x11_acknowledged_held_coverage_lower_ms": ms(total_confirmed_ns),
            "x11_acknowledged_held_coverage_upper_ms": ms(total_possible_ns),
            "no_held_input_lower_ms": ms(total_wait - total_possible_ns),
            "no_held_input_upper_ms": ms(total_wait - total_confirmed_ns),
            "independent_kills_final": score["kill_count"],
            "independent_deaths_final": score["death_count"],
            "independent_map_exit_final": score["map_exit"],
        },
        "useful_effect_timing": {
            "status": "UNAVAILABLE",
            "reason": ("retained independent scorer is terminal/final; typed health/ammo "
                       "and viewport changes are controller-observable or non-semantic and "
                       "must not be relabelled as an independently timed first useful effect"),
        },
        "measurement_scope": (
            "X11-synchronized key-down acknowledgement with conservative normal-release "
            "brackets; not an independent query of physical key state at every instant"),
    }


def main():
    if OUT.exists():
        raise FileExistsError(OUT)
    runs = [analyze_run(name) for name in RUNS]
    result = {
        "schema": "map01-v38-v39-useful-control-posthoc-v1",
        "analysis_kind": "descriptive retained-evidence reconstruction",
        "runs": runs,
        "source_semantics": {
            "held_start": (
                "keys_held.input_ack_ns follows all per-key X11 input acknowledgements"),
            "normal_release_bracket": (
                "frozen hold implementation captures loop observations before key-up, "
                "then synchronizes key-up and captures one final observation before "
                "step_completed"),
            "interrupted_release": (
                "input_released.owner_release.verified_ns proves empty owner state only "
                "as an upper release bound; cancellation publication is not used as a "
                "strict lower bound"),
        },
        "limits": [
            "No per-key normal key-up timestamp was retained.",
            "Key-down acknowledgement is X11-synchronized but not an independent keyboard bitmap sample.",
            "No retained timestamped independent first-useful-effect oracle was found.",
            "This is posthoc descriptive evidence and does not establish causal v38-v39 improvement.",
        ],
    }
    OUT.mkdir()
    (OUT / "analysis.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({row["run"]: row["totals"] for row in runs}, indent=2))


if __name__ == "__main__":
    main()
