"""Independent streaming raw-only reference; does not import candidate or runner."""
import copy
import gzip
import itertools
import json
import sys
from pathlib import Path


EVENTS = ("INVALIDATE", "POLL", "OBS_MATCH", "OBS_UNLINKED", "OBS_REPLAY", "OBS_OLD_REQUEST", "ACT")


def reference(word):
    gen, seq, obs_gen, stale = 0, 0, 0, False
    waiting, floor, serial, superseded = None, None, 0, None
    reqs, obs, acts = [], [], []
    for event in word:
        if event == "INVALIDATE":
            superseded, waiting, floor = waiting, None, None
            gen += 1
            stale, obs_gen = True, -1
        elif event == "POLL":
            if stale and waiting is None:
                serial += 1
                waiting, floor = "req-%d" % serial, seq
                reqs.append({"id": waiting, "generation": gen, "after_seq": floor})
        elif event in ("OBS_MATCH", "OBS_UNLINKED", "OBS_REPLAY", "OBS_OLD_REQUEST"):
            claim, n = waiting, seq + 1
            if event == "OBS_UNLINKED":
                claim = None
            elif event == "OBS_REPLAY":
                n = seq if floor is None else floor
            elif event == "OBS_OLD_REQUEST":
                claim = superseded if superseded is not None else "no-prior-request"
            valid = waiting is not None and claim == waiting and floor is not None and n > floor
            obs.append({"event": event, "request_id": claim, "generation": gen,
                        "seq": n, "linked": bool(valid)})
            if valid:
                seq, obs_gen, stale, waiting, floor = n, gen, False, None, None
        elif event == "ACT":
            acts.append({"generation": gen, "admitted": bool(not stale and obs_gen == gen)})
        else:
            raise ValueError("unknown event in oracle")
    return {"trace": list(word), "requests": reqs, "observations": obs, "actions": acts,
            "final": {"generation": gen, "observation_seq": seq, "observed_generation": obs_gen,
                      "stale": stale, "pending_id": waiting, "request_counter": serial}}


def compare(row, word):
    return row == reference(word)


def audit_file(path, expected):
    with gzip.open(path, "rt", encoding="utf-8", newline="") as stream:
        index = 0
        for length in range(expected["max_trace_length"] + 1):
            for word in itertools.product(EVENTS, repeat=length):
                line = stream.readline()
                if not line:
                    return ["row:%d:missing" % index], index
                try:
                    row = json.loads(line)
                except Exception:
                    return ["row:%d:json" % index], index
                if not compare(row, word):
                    return ["row:%d:reference_mismatch" % index], index
                index += 1
        if stream.readline():
            return ["extra_rows"], index
    if index != expected["trace_count"]:
        return ["trace_count"], index
    return [], index


def mutation_controls():
    controls = {}
    # Each synthetic corruption is checked against its own independently generated reference.
    word = ("INVALIDATE", "POLL", "ACT")
    row = reference(word)
    bad = copy.deepcopy(row); bad["actions"][0]["admitted"] = True
    controls["accept_stale_action"] = not compare(bad, word)

    word = ("INVALIDATE", "POLL", "OBS_UNLINKED", "ACT")
    row = reference(word)
    bad = copy.deepcopy(row); bad["observations"][0]["linked"] = True
    controls["clear_on_unlinked"] = not compare(bad, word)

    word = ("INVALIDATE", "POLL", "INVALIDATE", "POLL", "OBS_OLD_REQUEST", "ACT")
    row = reference(word)
    bad = copy.deepcopy(row); bad["observations"][0]["linked"] = True
    controls["accept_superseded_response"] = not compare(bad, word)

    word = ("INVALIDATE", "POLL", "POLL")
    row = reference(word)
    bad = copy.deepcopy(row); bad["requests"].append(copy.deepcopy(bad["requests"][0]))
    controls["duplicate_pending_request"] = not compare(bad, word)

    word = ()
    row = reference(word)
    bad = copy.deepcopy(row); bad["trace"].append("ACT")
    controls["change_trace"] = not compare(bad, word)
    return controls


if __name__ == "__main__":
    root = Path(__file__).resolve().parent
    expected = json.loads((root / "expected.json").read_text(encoding="utf-8"))
    errors, count = audit_file(Path(sys.argv[1]), expected)
    controls = mutation_controls()
    missed = [key for key, rejected in controls.items() if not rejected]
    result = {"passed": not errors and not missed, "errors": errors, "rows_audited": count,
              "mutation_controls": {"rejected": sum(controls.values()), "total": len(controls),
                                    "results": controls}, "missed_mutations": missed}
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["passed"] else 1)
