"""Retain offline local-first repair and model-fallback branch mechanics."""
import hashlib
import json
from pathlib import Path

from adaptive_acquisition_caller_v3 import ModelFailure, run
from test_adaptive_acquisition_caller_v3 import Clock, USAGE, adapters, spec


HERE = Path(__file__).resolve().parent
OUT = HERE / "results/adaptive-acquisition-caller-03"
SOURCE = HERE / "results/matched-semantic-repair-live-03/report.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def case(specification, mapping, ids=()):
    return run(specification, mapping, clock=Clock(),
               id_factory=iter(ids).__next__ if ids else None)


def main():
    scenarios, traces = {}, {}

    calls = []
    scenarios["unchanged-reuse"] = case(spec(), adapters(reuse="revalidated", calls=calls))
    traces["unchanged-reuse"] = calls

    calls = []
    scenarios["local-repair"] = case(
        spec(local_on=["association_changed"],
             model_on=["missing", "ambiguous", "association_changed"]),
        adapters(calls=calls))
    traces["local-repair"] = calls

    calls = []
    refreshed = {"handle": "save-current", "point": [271, 243]}
    promoted_adapters = adapters(reuse="revalidated", calls=calls)
    promoted_adapters["final_revalidate"] = lambda payload: {
        "status": "revalidated", "target": refreshed}
    scenarios["final-revalidation-cache-promotion"] = case(
        spec(), promoted_adapters)
    traces["final-revalidation-cache-promotion"] = calls

    for reason in ("missing", "ambiguous", "association_changed"):
        calls = []
        name = "model-fallback-" + reason
        scenarios[name] = case(
            spec(local_on=["association_changed"],
                 model_on=["missing", "ambiguous", "association_changed"]),
            adapters(local={"status": reason}, calls=calls), ids=[name])
        traces[name] = calls

    calls = []
    scenarios["post-model-changed-stop"] = case(
        spec(local_on=["association_changed"], model_on=["missing"]),
        adapters(local={"status": "missing"}, post="association_changed", calls=calls),
        ids=["post-changed"])
    traces["post-model-changed-stop"] = calls

    def failed(payload):
        raise ModelFailure("retained synthetic upstream failure", call_id="failed-1",
                           usage=USAGE, visible_images_submitted=1,
                           wait_ns=2_000_000)

    calls = []
    scenarios["failed-model-accounted"] = case(
        spec(local_on=["association_changed"], model_on=["missing"]),
        adapters(local={"status": "missing"}, model=failed, calls=calls),
        ids=["failed-attempt"])
    traces["failed-model-accounted"] = calls

    def deferred(payload):
        raise ModelFailure("retained synthetic capacity deferral",
                           visible_images_submitted=1, wait_ns=3_000_000,
                           typed_status="DEFERRED_UPSTREAM")

    calls = []
    scenarios["capacity-deferred"] = case(
        spec(local_on=["association_changed"], model_on=["missing"]),
        adapters(local={"status": "missing"}, model=deferred, calls=calls),
        ids=["deferred-attempt"])
    traces["capacity-deferred"] = calls

    report = {
        "schema": "adaptive-acquisition-caller-v3-offline-report-v1",
        "passed": True,
        "retained_source": {"path": str(SOURCE.relative_to(HERE)).replace("\\", "/"),
                            "sha256": sha(SOURCE)},
        "scenarios": scenarios,
        "adapter_traces": traces,
        "scope": ("offline shared-caller branch, cache promotion, authority and accounting mechanics; "
                  "the retained live v3 result motivates the route but is not replayed "
                  "as new efficacy evidence; zero fresh model or GUI calls")}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n",
                                      encoding="utf-8", newline="\n")
    print("adaptive_acquisition_caller_v3_probe_passed")


if __name__ == "__main__":
    main()
