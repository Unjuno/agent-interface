"""Probe strict accept-or-expand anchor receipt binding."""
import json

from anchor_evidence_contract_v1 import validate


READY = {"status": "READY", "binding": {"surface": 7}, "receipts": [{
    "receipt_index": 1, "point": [12, 34], "tooltip": {"pixels_sha256": "a"}}]}
BASE = {"op": "target_reference", "receipt_index": 1,
        "point_space": "source_observation_pixels", "point": {"x": 12, "y": 34},
        "motion_model": "surface_origin_translation",
        "evidence_kind": "persistent_hover_tooltip"}


def refused(value, readiness=READY):
    try:
        validate(value, readiness)
    except ValueError:
        return True
    return False


def main():
    assert validate(BASE, READY)["status"] == "EVIDENCE_BOUND"
    expand = dict(BASE, op="expand_search")
    assert validate(expand, READY)["status"] == "EXPANSION_REQUIRED"
    controls = [dict(BASE, receipt_index=2), dict(BASE, point={"x": 13, "y": 34}),
                dict(BASE, motion_model="not_applicable"),
                {key: value for key, value in BASE.items() if key != "point"},
                dict(BASE, extra=True)]
    assert all(refused(value) for value in controls)
    assert refused(BASE, {"status": "READY", "receipts": []})
    assert refused(BASE, {"status": "READY", "receipts": READY["receipts"] * 2})
    print(json.dumps({"accept_bound": True, "expand_bound": True,
                      "invalid_controls_refused": len(controls) + 2}))


if __name__ == "__main__":
    main()
