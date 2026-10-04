"""No-GUI branch checks for receipt-to-target admission."""
import copy

from PIL import Image

from receipt_target_admission_v1 import dispatch, evaluate


def observation(sequence, capture_ns=1_000_000, geometry=None):
    return {"sequence": sequence, "capture_ns": capture_ns,
            "pointer_binding": {"focus": 10, "surface": 20,
                                "geometry": geometry or [0, 0, 120, 100]}}


def images():
    baseline = Image.new("RGB", (120, 100), "black")
    receipt = baseline.copy()
    current = baseline.copy()
    for image, color in ((receipt, "red"), (current, "blue")):
        image.paste(color, (30, 30, 50, 50))
    for image in (baseline, receipt, current):
        image.paste("green", (80, 10, 100, 30))
    return baseline, receipt, current


def specification():
    return {"target": "directly_above_copper_source",
            "point_space": "source_observation_pixels",
            "motion_model": "surface_origin_translation",
            "point": [40, 40], "source_sequence": 2,
            "decision_after_sequence": 2, "ttl_ms": 60000,
            "freshness_ms": 1000,
            "checks": [
                {"kind": "exact_patch", "source_sequence": 1,
                 "box": [80, 10, 100, 30]},
                {"kind": "stable_change_mask", "baseline_sequence": 1,
                 "receipt_sequence": 2, "box": [20, 20, 60, 60],
                 "minimum_changed_pixels": 300},
            ]}


def main():
    baseline, receipt, current = images()
    history = {1: {"observation": observation(1), "image": baseline},
               2: {"observation": observation(2), "image": receipt}}
    fresh = observation(3, 1_500_000)
    calls = []
    accepted = dispatch(specification(), history, fresh, current, 1_600_000,
                        lambda point, deadline: calls.append((point, deadline)) or "clicked",
                        clock=iter([2_000_000, 2_000_050]).__next__)
    assert accepted["eligible"] and accepted["adapter_called"]
    assert accepted["point"] == [40, 40] and accepted["check_to_adapter_ns"] == 50
    assert calls == [([40, 40], 1_001_500_000)]

    controls = {}
    changed_exact = current.copy(); changed_exact.paste("yellow", (80, 10, 100, 30))
    controls["changed_exact"] = evaluate(specification(), history, fresh,
                                                  changed_exact, 1_600_000)
    changed_mask = current.copy(); changed_mask.paste("blue", (55, 55, 58, 58))
    controls["changed_mask"] = evaluate(specification(), history, fresh,
                                                 changed_mask, 1_600_000)
    controls["missing_history"] = evaluate(specification(), {2: history[2]}, fresh,
                                                    current, 1_600_000)
    controls["clock_only"] = evaluate(specification(), history, observation(2, 1_500_000),
                                              current, 1_600_000)
    stale = copy.deepcopy(fresh); stale["capture_ns"] = 1_000_000
    controls["stale"] = evaluate(specification(), history, stale, current,
                                         1_002_000_000)
    changed_focus = copy.deepcopy(fresh); changed_focus["pointer_binding"]["focus"] = 30
    controls["changed_focus"] = evaluate(specification(), history, changed_focus,
                                                 current, 1_600_000)
    resized = copy.deepcopy(fresh); resized["pointer_binding"]["geometry"][2] = 121
    controls["resized_surface"] = evaluate(specification(), history, resized,
                                                   current, 1_600_000)
    translated = copy.deepcopy(fresh); translated["pointer_binding"]["geometry"] = [5, 7, 120, 100]
    translated_image = Image.new("RGB", (120, 100), "black")
    translated_image.paste("blue", (35, 37, 55, 57))
    translated_image.paste("green", (85, 17, 105, 37))
    controls["translated"] = evaluate(specification(), history, translated,
                                              translated_image, 1_600_000)
    expected = {"changed_exact": "exact_dependency_changed",
                "changed_mask": "stable_change_mask_changed",
                "missing_history": "historical_evidence_unavailable",
                "clock_only": "no_post_decision_observation",
                "stale": "current_evidence_stale",
                "changed_focus": "focus_or_surface_changed",
                "resized_surface": "surface_size_changed"}
    for name, reason in expected.items():
        assert controls[name]["eligible"] is False
        assert controls[name]["authority_class"] == "NO_TARGET_AUTHORITY"
        assert controls[name]["point"] is None and controls[name]["reason"] == reason
    assert controls["translated"]["eligible"] is True
    assert controls["translated"]["point"] == [45, 47]
    blocked_calls = []
    blocked = dispatch(specification(), history, fresh, changed_mask, 1_600_000,
                       lambda point, deadline: blocked_calls.append((point, deadline)))
    assert blocked["adapter_called"] is False and blocked_calls == []
    print("receipt_target_admission_v1_probe_passed")


if __name__ == "__main__":
    main()
