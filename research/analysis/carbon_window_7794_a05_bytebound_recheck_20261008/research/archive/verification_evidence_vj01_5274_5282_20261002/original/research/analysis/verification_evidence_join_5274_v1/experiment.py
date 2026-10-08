"""Run one finite synthetic allocation; no model, GUI, input or network."""
from __future__ import annotations
import argparse
import csv
import hashlib
import itertools
import json
import os
from pathlib import Path
import platform
import sys
import time
from reducer import Reducer

ROOT = Path(__file__).resolve().parent
NAMES = ("target", "effect", "diagnostic")
COLUMNS = ("case", "order", "prefix", "final", "late", "naive", "authority", "rejected")


def event(check: str, value: str = "PASS", **extra: object) -> dict:
    x = dict(rid=check, check=check, subject=check, session="session-vj01",
             decision="decision-vj01", epoch=7,
             role="VERIFIED_EFFECT" if check == "effect" else "CURRENT", value=value)
    x.update(extra)
    return x


def variant(check: str, code: int) -> dict | None:
    if code == 0:
        return None
    value = ("PASS", "FAIL", "UNKNOWN", "TIMEOUT")[code-1] if code <= 4 else "PASS"
    x = event(check, value)
    if code >= 5:
        x["role"] = {5: "HISTORICAL", 6: "PREDICTED",
                     7: "CURRENT" if check == "effect" else "VERIFIED_EFFECT"}[code]
    return x


def prepare() -> None:
    t, e, d = event("target"), event("effect"), event("diagnostic")
    missing = event("target"); del missing["value"]
    specs = [
        ("duplicate", [t, e, dict(t)], "P"),
        ("mandatory_conflict", [t, e, event("target", "FAIL", rid="t2")], "U"),
        ("id_collision", [t, e, event("target", "FAIL")], "U"),
        ("optional_conflict", [t, e, d, event("diagnostic", "FAIL", rid="d2")], "U"),
        ("mandatory_veto", [event("target", "FAIL"), e, d], "F"),
        ("veto_over_other_conflict", [event("target", "FAIL"), e, event("effect", "FAIL", rid="e2")], "F"),
        ("pass_plus_unknown", [t, e, event("target", "UNKNOWN", rid="t2")], "U"),
        ("fail_plus_unknown", [event("target", "FAIL"), e, event("target", "UNKNOWN", rid="t2")], "F"),
        ("wrong_session", [event("target", session="other"), e], "U"),
        ("wrong_decision", [event("target", decision="other"), e], "U"),
        ("wrong_epoch", [event("target", epoch=8), e], "U"),
        ("wrong_subject", [event("target", subject="effect"), e], "U"),
        ("stale_irrelevant", [t, e, event("target", "FAIL", epoch=8)], "P"),
        ("bool_epoch", [event("target", epoch=True), e], "U"),
        ("extra_authority", [event("target", authority=True), e], "U"),
        ("missing_value", [missing, e], "U"),
        ("unknown_check", [t, e, event("unregistered")], "U"),
        ("unknown_role", [t, e, event("target", role="ASSERTED", rid="t2")], "U"),
        ("optional_timeout", [t, e, event("diagnostic", "TIMEOUT")], "P"),
        ("non_object", [t, e, []], "U"),
        ("collision_with_other_veto", [t, event("target", "FAIL"), event("effect", "FAIL")], "F"),
        ("complete_positive", [t, e, d], "P"),
    ]
    with (ROOT / "DIRECTED.json").open("x", encoding="utf-8") as f:
        json.dump([dict(name=n, events=ev, expected=ex) for n, ev, ex in specs], f, indent=2)
        f.write("\n")
    print(json.dumps({"prepared_directed_cases": len(specs), "formal_invocations": 0}))


def cases():
    for codes in itertools.product(range(8), repeat=3):
        es = [variant(n, c) for n, c in zip(NAMES, codes)]
        yield "M" + "".join(map(str, codes)), [e for e in es if e is not None]
    for i, spec in enumerate(json.loads((ROOT / "DIRECTED.json").read_text())):
        yield "D%02d" % i, spec["events"]


def run(output: Path) -> None:
    freeze = json.loads((ROOT / "FREEZE.json").read_text())
    for name, record in freeze["files"].items():
        data = (ROOT / name).read_bytes()
        if len(data) != record["bytes"] or hashlib.sha256(data).hexdigest() != record["sha256"]:
            raise RuntimeError("SOURCE_MISMATCH:" + name)
    output.mkdir(parents=True, exist_ok=False)
    started = dict(allocation=freeze["allocation"], argv=sys.argv, python=sys.version,
                   platform=platform.platform(), executable=sys.executable,
                   start_ns=time.monotonic_ns(), authority=False, source_main=freeze["source_main"],
                   freeze_sha256=hashlib.sha256((ROOT / "FREEZE.json").read_bytes()).hexdigest())
    (output / "RUN_STARTED.json").write_text(json.dumps(started, indent=2) + "\n")
    rows = 0
    with (output / "raw.csv").open("x", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, lineterminator="\n")
        writer.writeheader()
        for case, events in cases():
            for order in itertools.permutations(range(len(events))):
                reducer = Reducer()
                prefix = reducer.view()
                delivered = [events[i] for i in order]
                for item in delivered:
                    prefix += reducer.feed(item)
                final = reducer.seal()
                late = reducer.feed(event("target", "FAIL", rid="late-f"))
                late += reducer.feed(event("target", "PASS", rid="late-p"))
                late += reducer.seal()
                last = delivered[-1] if delivered and isinstance(delivered[-1], dict) else {}
                naive = {"PASS": "P", "FAIL": "F"}.get(last.get("value"), "U")
                writer.writerow(dict(case=case, order="".join(map(str, order)) or "-",
                                     prefix=prefix, final=final, late=late, naive=naive,
                                     authority=int(reducer.authority), rejected=reducer.rejected))
                rows += 1
            f.flush()
        os.fsync(f.fileno())
    raw = (output / "raw.csv").read_bytes()
    (output / "RUN_FINISHED.json").write_text(json.dumps(dict(
        allocation=freeze["allocation"], rows=rows, end_ns=time.monotonic_ns(),
        raw_bytes=len(raw), raw_sha256=hashlib.sha256(raw).hexdigest(),
        formal_invocations=1, retries=0, model_calls=0, gui_calls=0, authority=False), indent=2) + "\n")
    print(json.dumps({"rows": rows, "raw_sha256": hashlib.sha256(raw).hexdigest()}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--run", type=Path)
    args = parser.parse_args()
    if args.prepare == bool(args.run):
        parser.error("provide exactly one of --prepare / --run")
    prepare() if args.prepare else run(args.run)
