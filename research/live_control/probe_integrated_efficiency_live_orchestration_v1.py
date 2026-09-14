"""Zero-model composed-path probe for the formal live runner."""

import json
from pathlib import Path

import run_integrated_efficiency_live_v1 as live
from integrated_efficiency_protocol_v1 import ARMS, evaluate


HERE = Path(__file__).resolve().parent
OUT = HERE / "results" / "integrated-efficiency-live-orchestration-probe-02"
POINTS = {"A": {"field_point": [226, 401], "submit_point": [376, 401]},
          "B": {"field_point": [650, 558], "submit_point": [688, 634]}}
USAGE = {"input_tokens": 1000, "cached_input_tokens": 0,
         "cache_write_input_tokens": 0, "output_tokens": 10,
         "reasoning_output_tokens": 0}


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    (OUT / "workspaces").mkdir()
    live.OUT = OUT
    arms, independent, call_ids = {}, {}, []
    for arm in ARMS:
        count = 0

        def fake_call(_root, _prompt, _image, contract, _workspace):
            nonlocal count
            count += 1
            layout = ("A" if (arm != "persistent" and count <= 3)
                      or (arm == "persistent" and count == 1) else "B")
            call_id = f"engineering:{arm}:{count}"
            call_ids.append(call_id)
            grounding = dict(POINTS[layout])
            if contract == "compiled":
                grounding["method"] = {"engineering": "fixed"}
            return {"grounding": grounding, "usage": dict(USAGE),
                    "call_id": call_id, "runner_ns": 0,
                    "requested_model": "synthetic-no-model",
                    "requested_effort": "none", "cost": None}

        live.call_model = fake_call
        workspace = OUT / "workspaces" / arm
        workspace.mkdir()
        arms[arm], independent[arm] = live.run_arm(arm, 991028, workspace)
    preflights = {arm: {"call_id": f"engineering:preflight:{arm}",
        "stage": "schema_preflight", "requested_model": "synthetic-no-model",
        "requested_effort": "none", "usage": dict(USAGE),
        "model_visible_images": 0} for arm in ARMS}
    trace = {"schema": "integrated_efficiency_trace_v1", "arms": arms,
             "preflight_calls": preflights,
             "integration_discoveries": json.loads(
                 (HERE / "integrated_efficiency_discoveries_v1.json").read_text())}
    evaluation = evaluate(trace)
    assert evaluation["disposition"] == "RETAIN"
    assert all(independent[arm]["success"] is True for arm in ARMS)
    assert len(call_ids) == 14 and len(set(call_ids)) == 14
    report = {"schema": "integrated_efficiency_live_orchestration_probe_v1",
              "passed": True, "model_calls": 0,
              "synthetic_grounding_invocations": len(call_ids),
              "independent_success": {arm: independent[arm]["success"] for arm in ARMS},
              "protocol_disposition_with_synthetic_usage": evaluation["disposition"],
              "claim": "engineering orchestration only; excluded from formal comparison"}
    live.dump(OUT / "report.json", report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
