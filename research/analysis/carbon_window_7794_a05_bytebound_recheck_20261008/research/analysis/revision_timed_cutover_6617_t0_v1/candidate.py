#!/usr/bin/env python3
"""Finite logical-time simulator for Issue #6617 T0; no audio, model, or GUI."""
import argparse
import json
from pathlib import Path


ARMS = ("final_only", "naive_provisional", "version_bound_read_only")


def event(events, kind, time, **fields):
    events.append({"kind": kind, "time": time, **fields})


def run_case(case, default_prep):
    rows = []
    if case["id"] == "C10":
        for arm in ARMS:
            ev = []
            event(ev, "held_input_start", 0, key="KEY_A", authority="preexisting")
            event(ev, "urgent_interrupt", 2, source="independent_release_channel")
            event(ev, "physical_release", 2, key="KEY_A", trigger="urgent_interrupt")
            event(ev, "release_verified", 3, key="KEY_A", verified=True)
            event(ev, "planner_completion", 20)
            rows.append({"scenario_id": case["id"], "arm": arm, "events": ev})
        return rows

    p = case["partial"]
    f = case["final"]
    prep = default_prep
    partial_prep = case.get("partial_preparation_ticks", prep)
    for arm in ARMS:
        ev = []
        event(ev, "provisional", 0, turn=p["turn"], epoch=p["epoch"],
              principal=p["principal"], intent=p["intent"], speech_act=p["speech_act"])
        if "revision" in case:
            event(ev, "revision", case["revision"]["time"], turn=p["turn"],
                  epoch=case["revision"]["epoch"], intent=case["revision"]["intent"])
        if arm == "naive_provisional":
            done = partial_prep
            event(ev, "readonly_prepare_start", 0, turn=p["turn"], epoch=p["epoch"], intent=p["intent"])
            event(ev, "readonly_prepare_complete", done, turn=p["turn"], epoch=p["epoch"], intent=p["intent"])
            input_time = done + 1
            if case.get("stop") == "before_input":
                stop_time = 11
                if input_time >= stop_time:
                    event(ev, "stop", stop_time, order="before_input")
                    event(ev, "physical_release", stop_time, key="KEY_A", trigger="stop")
                    event(ev, "release_verified", stop_time + 1, key="KEY_A", verified=True)
                else:
                    issue_input(ev, input_time, p["turn"], p["epoch"], p["principal"], p["intent"],
                                authenticated=False, committed=False, provisional=True)
                    event(ev, "effect_verified", input_time + 2, intent=p["intent"], verified=True, reversible=False)
                    event(ev, "stop", stop_time, order="after_verified_effect")
                    event(ev, "effect_disposition", stop_time, status="already_occurred", automatic_undo=False, fresh_remedy_required=True)
            else:
                issue_input(ev, input_time, p["turn"], p["epoch"], p["principal"], p["intent"],
                            authenticated=False, committed=False, provisional=True)
                if case.get("stop") == "after_input_effect_unknown":
                    event(ev, "effect_unknown", input_time + 1, intent=p["intent"])
                    event(ev, "stop", input_time + 1, order="after_input_before_effect_confirmation")
                    event(ev, "retry", input_time + 2, allowed=False, reason="effect_unknown")
                    event(ev, "blind_inverse", input_time + 2, allowed=False, reason="effect_unknown")
                elif case.get("stop") == "after_verified_irreversible_effect":
                    event(ev, "effect_verified", input_time + 1, intent=p["intent"], verified=True, reversible=False)
                    event(ev, "stop", input_time + 2, order="after_verified_effect")
                    event(ev, "effect_disposition", input_time + 2, status="already_occurred", automatic_undo=False, fresh_remedy_required=True)
                else:
                    event(ev, "effect_verified", input_time + 2, intent=p["intent"], verified=True)
        else:
            event(ev, "final", f["time"], turn=f["turn"], version=f["version"],
                  principal=f["principal"], intent=f["intent"], speech_act=f["speech_act"],
                  authenticated=f["authenticated"], committed=f["committed"])
            same_epoch = (p["turn"] == f["turn"] and p["principal"] == f["principal"]
                          and p["intent"] == f["intent"] and p["speech_act"] == "request"
                          and f["speech_act"] == "request")
            valid = f["authenticated"] is True and f["committed"] is True and f["speech_act"] == "request"
            if arm == "version_bound_read_only" and not valid:
                event(ev, "readonly_prepare_start", 0, turn=p["turn"], epoch=p["epoch"], intent=p["intent"])
                event(ev, "readonly_prepare_complete", partial_prep, turn=p["turn"], epoch=p["epoch"], intent=p["intent"])
                event(ev, "prepared_candidate_disposition", case.get("revision", {}).get("time", f["time"]),
                      turn=p["turn"], epoch=p["epoch"], disposition="discarded_final_not_effectful_request")
            if valid:
                if arm == "version_bound_read_only" and same_epoch:
                    event(ev, "readonly_prepare_start", 0, turn=p["turn"], epoch=p["epoch"], intent=p["intent"])
                    event(ev, "readonly_prepare_complete", prep, turn=p["turn"], epoch=p["epoch"], intent=p["intent"])
                    event(ev, "prepared_candidate_disposition", f["time"], turn=p["turn"], epoch=p["epoch"], disposition="reused_after_exact_version_check")
                    input_time = f["time"] + 1
                else:
                    if arm == "version_bound_read_only":
                        event(ev, "readonly_prepare_start", 0, turn=p["turn"], epoch=p["epoch"], intent=p["intent"])
                        event(ev, "readonly_prepare_complete", partial_prep, turn=p["turn"], epoch=p["epoch"], intent=p["intent"])
                        event(ev, "prepared_candidate_disposition", case.get("revision", {}).get("time", f["time"]),
                              turn=p["turn"], epoch=p["epoch"], disposition="discarded_version_or_principal_mismatch")
                    event(ev, "readonly_prepare_start", f["time"], turn=f["turn"], version=f["version"], intent=f["intent"])
                    event(ev, "readonly_prepare_complete", f["time"] + prep, turn=f["turn"], version=f["version"], intent=f["intent"])
                    input_time = f["time"] + prep + 1
                issue_input(ev, input_time, f["turn"], f["version"], f["principal"], f["intent"],
                            authenticated=True, committed=True, provisional=False)
                stop = case.get("stop")
                if stop == "before_input":
                    stop_time = 11
                    if input_time >= stop_time:
                        ev[:] = [x for x in ev if not (x["kind"] == "consequential_input" and x["time"] == input_time)]
                        ev[:] = [x for x in ev if not (x["kind"] == "effect_verified")]
                        event(ev, "stop", stop_time, order="before_input")
                        event(ev, "physical_release", stop_time, key="KEY_A", trigger="stop")
                        event(ev, "release_verified", stop_time + 1, key="KEY_A", verified=True)
                    else:
                        event(ev, "stop", stop_time, order="after_verified_effect")
                        event(ev, "effect_disposition", stop_time, status="already_occurred", automatic_undo=False, fresh_remedy_required=True)
                elif stop == "after_input_effect_unknown":
                    ev[:] = [x for x in ev if x["kind"] not in ("effect_verified",)]
                    event(ev, "effect_unknown", input_time + 1, intent=f["intent"])
                    event(ev, "stop", input_time + 1, order="after_input_before_effect_confirmation")
                    event(ev, "retry", input_time + 2, allowed=False, reason="effect_unknown")
                    event(ev, "blind_inverse", input_time + 2, allowed=False, reason="effect_unknown")
                elif stop == "after_verified_irreversible_effect":
                    event(ev, "effect_verified", input_time + 1, intent=f["intent"], verified=True, reversible=False)
                    event(ev, "stop", input_time + 2, order="after_verified_effect")
                    event(ev, "effect_disposition", input_time + 2, status="already_occurred", automatic_undo=False, fresh_remedy_required=True)
                else:
                    event(ev, "effect_verified", input_time + 2, intent=f["intent"], verified=True)
        rows.append({"scenario_id": case["id"], "arm": arm, "events": sorted(ev, key=lambda x: (x["time"], x["kind"]))})
    return rows


def issue_input(ev, time, turn, version, principal, intent, **proof):
    event(ev, "consequential_input", time, turn=turn, version=version, principal=principal,
          intent=intent, **proof)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    spec = json.loads(Path(a.cases).read_text(encoding="utf-8"))
    rows = []
    for case in spec["cases"]:
        rows.extend(run_case(case, spec["preparation_ticks"]))
    Path(a.out).write_text(json.dumps({"schema":"revision-timed-cutover-raw-v1","rows":rows}, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    print(json.dumps({"rows":len(rows),"arms":len(ARMS),"scenarios":len(spec["cases"])}))


if __name__ == "__main__":
    main()
