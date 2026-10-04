"""Offline construction oracle for per-key release bounds and useful feedback.

This deliberately consumes only synthetic receipts. It defines a conservative
measurement contract; it does not infer missing physical key-up events from
program completion or image change.
"""
from __future__ import annotations

from collections import defaultdict
from independent_progress_clock_v1 import ProgressClock, ProgressSample


SCORE_FIELDS = ("map_exit", "episode_finished", "player_dead", "death_count",
                "kill_count")


def reconcile_key_intervals(events):
    """Join ordinary release brackets and batch cleanup intervals by identity.

    The release transition is interval-censored between caller start/return;
    it is never treated as an exact physical key-up timestamp. Ordinary up
    receipts need evidence that a key release was actually applied and carry
    the resolved keycode. Cancellation intervals use resolved X keycodes and
    collapse aliases into one physical key group. Missing identity falls back
    only to the broad verified-owner censoring bound.
    """
    opens = defaultdict(list)
    intervals = []
    errors = []
    for row in events:
        kind = row.get("event")
        if kind == "input_admission":
            token = row.get("intent_token")
            # Program ID is distinct from the lease token. Keep it in the join
            # so repeated step/key values from separate programs cannot steal
            # each other's release receipt.
            key = (token, row.get("id"), row.get("step"), row.get("key"))
            admitted, ack = row.get("admitted_ns"), row.get("input_ack_ns")
            if (not isinstance(token, str) or not token or type(row.get("step")) is not int
                    or not isinstance(row.get("id"), str) or not row.get("id")
                    or not isinstance(row.get("key"), str) or not row.get("key")
                    or not isinstance(row.get("owner_id"), str) or not row.get("owner_id")
                    or (row.get("keycode") is not None and
                        (type(row.get("keycode")) is not int or row["keycode"] <= 0))
                    or type(admitted) is not int or type(ack) is not int
                    or admitted > ack):
                errors.append("invalid_admission")
            else:
                opens[key].append({"owner_id": row["owner_id"],
                                   "id": row["id"], "step": row["step"],
                                   "key": row["key"],
                                   "keycode": row.get("keycode"),
                                   "admitted_ns": admitted, "ack_ns": ack})
        elif kind == "input_release_rpc":
            token = row.get("intent_token")
            key = (token, row.get("id"), row.get("step"), row.get("payload"))
            interval = row.get("release_transition_interval_ns")
            opened = opens.get(key, [])
            if (row.get("operation") != "up" or not opened or
                    type(interval) is not list or len(interval) != 2 or
                    any(type(value) is not int for value in interval) or
                    interval[0] > interval[1] or
                    row.get("call_started_ns") != interval[0] or
                    row.get("call_returned_ns") != interval[1] or
                    row.get("interval_width_ns") != interval[1]-interval[0] or
                    row.get("owner_id") != opened[0]["owner_id"] or
                    row.get("release_applied") is not True or
                    type(row.get("keycode")) is not int or
                    row.get("keycode") != opened[0].get("keycode") or
                    row.get("x11_release_and_sync_completed_before_return") is not True or
                    row.get("grants_input_authority") is not False or
                    row.get("continuous_physical_state_sampled") is not False or
                    row.get("application_consumption_observed") is not False):
                errors.append("invalid_or_unmatched_release_rpc")
            else:
                start, end = interval
                opened_row = opened.pop(0)
                if start < opened_row["ack_ns"]:
                    errors.append("release_rpc_precedes_key_ack")
                else:
                    intervals.append({"intent_token": key[0], "id": key[1],
                                      "step": key[2], "key": key[3], "ack_ns": opened_row["ack_ns"],
                                      "release_transition_interval_ns": interval,
                                      "occupancy_lower_ns": start-opened_row["ack_ns"],
                                      "occupancy_upper_ns": end-opened_row["ack_ns"],
                                      "exact_key_up_time": None, "censored": False})
        elif kind in ("input_released", "input_release_unverified", "owner_release"):
            # Executor V13 publishes the owner receipt nested in its release
            # event; the intent token is on the outer event, not that receipt.
            receipt = row.get("owner_release")
            if (kind != "input_released" or row.get("grants_input_authority") is not False
                    or type(receipt) is not dict
                    or receipt.get("verified") is not True
                    or receipt.get("keys_down") != []
                    or receipt.get("buttons_down") != []
                    or type(receipt.get("verified_ns")) is not int):
                errors.append("unverified_owner_release")
                continue
            lease_id = row.get("intent_token")
            if not isinstance(lease_id, str) or not lease_id:
                errors.append("missing_release_intent")
                continue
            receipt_ns = receipt["verified_ns"]
            raw_key_intervals = receipt.get("key_release_intervals_ns", [])
            if type(raw_key_intervals) is not list:
                errors.append("invalid_keycode_release_intervals")
                continue
            by_keycode = {}
            for item in raw_key_intervals:
                if type(item) is not dict:
                    errors.append("invalid_keycode_release_intervals")
                    continue
                code, bracket = item.get("keycode"), item.get("interval_ns")
                if (type(code) is not int or code <= 0 or code in by_keycode
                        or type(bracket) is not list or len(bracket) != 2
                        or any(type(value) is not int for value in bracket)
                        or bracket[0] > bracket[1] or bracket[1] > receipt_ns):
                    errors.append("invalid_keycode_release_intervals")
                    continue
                by_keycode[code] = bracket

            pending = []
            for key in list(opens):
                if key[0] != lease_id:
                    continue
                pending.extend((key, opened) for opened in opens[key])
                del opens[key]

            grouped = defaultdict(list)
            censored = []
            for key, opened in pending:
                code = opened["keycode"]
                if type(code) is int and code in by_keycode:
                    grouped[code].append((key, opened))
                else:
                    censored.append((key, opened))

            for code, members in grouped.items():
                bracket = by_keycode[code]
                first_ack = min(opened["ack_ns"] for _, opened in members)
                if bracket[0] < first_ack:
                    errors.append("release_rpc_precedes_key_ack")
                    continue
                names = sorted({opened["key"] for _, opened in members})
                ids = {opened["id"] for _, opened in members}
                steps = {opened["step"] for _, opened in members}
                intervals.append({
                    "intent_token": lease_id,
                    "owner_id": members[0][1]["owner_id"],
                    "id": next(iter(ids)) if len(ids) == 1 else None,
                    "step": next(iter(steps)) if len(steps) == 1 else None,
                    "key": names[0] if len(names) == 1 else None,
                    "keys": names,
                    "keycode": code,
                    "admission_count": len(members),
                    "ack_ns": first_ack,
                    "release_transition_interval_ns": bracket,
                    "occupancy_lower_ns": bracket[0] - first_ack,
                    "occupancy_upper_ns": bracket[1] - first_ack,
                    "exact_key_up_time": None,
                    "censored": False,
                })

            for key, opened in censored:
                if receipt_ns < opened["ack_ns"]:
                    errors.append("release_precedes_key_ack")
                else:
                    intervals.append({"intent_token": key[0], "owner_id": opened["owner_id"],
                                      "id": key[1], "step": key[2], "key": key[3],
                                      "ack_ns": opened["ack_ns"],
                                      "release_transition_interval_ns": None,
                                      "occupancy_lower_ns": None,
                                      "occupancy_upper_ns": receipt_ns-opened["ack_ns"],
                                      "exact_key_up_time": None, "censored": True})
    if any(opens.values()):
        errors.append("open_key_interval")
    if errors:
        raise ValueError(",".join(sorted(set(errors))))
    return intervals


def _paired_sample(sample, observation):
    """Accept a scorer row only when it names the exact observation epoch."""
    if (type(sample) is not dict or type(observation) is not dict or
            observation.get("event") != "observation" or
            observation.get("exact") is not True or
            type(observation.get("id")) is not str or not observation["id"] or
            type(observation.get("sequence")) is not int or observation["sequence"] < 0 or
            type(observation.get("capture_ns")) is not int or observation["capture_ns"] < 0 or
            type(observation.get("pointer_binding")) is not dict or
            not observation["pointer_binding"] or
            sample.get("independent") is not True or
            sample.get("controller_visible") is not False or
            sample.get("observation_id") != observation["id"] or
            sample.get("observation_sequence") != observation["sequence"] or
            sample.get("observation_capture_ns") != observation["capture_ns"] or
            type(sample.get("sample_ns")) is not int or
            sample["sample_ns"] < observation["capture_ns"] or
            any(type(sample.get(field)) is not bool if field in
                ("map_exit", "episode_finished", "player_dead") else
                type(sample.get(field)) is not int
                for field in SCORE_FIELDS)):
        return None
    return sample


def classify_useful_feedback(before, after, *, before_observation,
                              after_observation):
    """Use scorer samples joined by identity to exact observations."""
    before = _paired_sample(before, before_observation)
    after = _paired_sample(after, after_observation)
    if before is None or after is None:
        return "unknown"
    if (after_observation["sequence"] <= before_observation["sequence"] or
            after_observation["capture_ns"] <= before_observation["capture_ns"] or
            after_observation["pointer_binding"] != before_observation["pointer_binding"] or
            before["sample_ns"] >= after_observation["capture_ns"]):
        return "unknown"
    try:
        clock = ProgressClock()
        previous = {field: before[field] for field in SCORE_FIELDS}
        current = {field: after[field] for field in SCORE_FIELDS}
        clock.ingest(ProgressSample(sample_ns=before["sample_ns"], **previous))
        events = clock.ingest(ProgressSample(sample_ns=after["sample_ns"], **current))
    except (TypeError, ValueError):
        return "unknown"
    if not events:
        return "no_scored_progress"
    adverse = any(event["polarity"] == "negative" for event in events)
    useful = any(event["useful"] is True for event in events)
    if adverse and useful:
        return "mixed_progress_and_adverse"
    if adverse:
        return "adverse_progress"
    if any(event["kind"] == "MAP_EXIT" for event in events):
        return "useful_terminal_progress"
    if useful:
        return "useful_progress"
    return "no_scored_progress"


def recovery_window(start_ns, deadline_ns, score_ns):
    """Validate a single independently scored recovery observation window."""
    if any(type(value) is not int for value in (start_ns, deadline_ns, score_ns)):
        return False
    return start_ns <= score_ns <= deadline_ns
