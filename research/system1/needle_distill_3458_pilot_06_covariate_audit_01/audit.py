"""Independent raw-data/model audit for Issue #3892; never imports runner.py."""
import hashlib
import json
import math
import sys
from pathlib import Path

import torch
from torch.nn import functional as F

EXPECTED_RESULT_SHA256 = "0878c39a68fe2abea218132b307ceff77df1e9a52291ba14186f2c8c423e37a7"
EXPECTED_RESULT_GIT_BLOB = "d6259323e86dba3ae12f76765aed62ab9d78dfa8"
SEEDS = (3467, 3468, 3469)
LABELS = ("CONTINUE", "CORRECT", "WATCH")
META = {"intent": "track_target", "scope": "local-servo", "epoch": 7}


def balanced_class(label, n, seed):
    """Independent transcription of the immutable pilot-04 data generator."""
    g = torch.Generator().manual_seed(seed)
    if label == 0:
        xy = (torch.rand(n, 2, generator=g) - .5) * .08
        velocity = (torch.rand(n, 2, generator=g) - .5) * .08
        confidence = .72 + .28 * torch.rand(n, 1, generator=g)
        visible = torch.ones(n, 1)
    elif label == 1:
        sign = torch.where(torch.rand(n, 1, generator=g) > .5, 1., -1.)
        dx = sign * (.15 + .80 * torch.rand(n, 1, generator=g))
        dy = (torch.rand(n, 1, generator=g) - .5) * 1.6
        xy = torch.cat([dx, dy], 1)
        velocity = (torch.rand(n, 2, generator=g) - .5) * .4
        confidence = .72 + .28 * torch.rand(n, 1, generator=g)
        visible = torch.ones(n, 1)
    elif label == 2:
        xy = (torch.rand(n, 2, generator=g) - .5) * 2.
        velocity = (torch.rand(n, 2, generator=g) - .5) * .8
        confidence = .72 * torch.rand(n, 1, generator=g)
        visible = torch.randint(0, 2, (n, 1), generator=g).float()
    else:
        raise ValueError("unknown class")
    return torch.cat([xy, velocity, confidence, visible], 1)


def shifted_class(label, n, seed):
    if label != 1:
        return balanced_class(label, n, seed)
    g = torch.Generator().manual_seed(seed)
    sign = torch.where(torch.rand(n, 1, generator=g) > .5, 1., -1.)
    dx = sign * (.071 + .078 * torch.rand(n, 1, generator=g))
    dy = (torch.rand(n, 1, generator=g) - .5) * .20
    velocity = (torch.rand(n, 2, generator=g) - .5) * .10
    confidence = .80 + .20 * torch.rand(n, 1, generator=g)
    visible = torch.ones(n, 1)
    return torch.cat([dx, dy, velocity, confidence, visible], 1)


def teacher(x):
    dx, dy, vx, vy, confidence, visible = x.unbind(-1)
    watch = (confidence < .72) | (visible < .5)
    settled = (dx.abs() < .06) & (dy.abs() < .06) & ((vx.abs() + vy.abs()) < .12)
    return torch.where(watch, 2, torch.where(settled, 0, 1)).long()


def compare_vector(actual, expected, tolerance=1e-6):
    if len(actual) != 6 or len(expected) != 6:
        return ["feature_width"]
    errors = []
    for i, (a, e) in enumerate(zip(actual, expected)):
        if not math.isfinite(float(a)) or not math.isfinite(float(e)) or abs(float(a) - float(e)) > tolerance:
            errors.append(f"feature_{i}_mismatch")
    return errors


def state_tensors(model_state):
    state = {}
    for name, entry in model_state.items():
        values = torch.tensor(entry["values"], dtype=torch.float32)
        if list(entry["shape"]) != list(values.reshape(entry["shape"]).shape):
            raise ValueError("model_state_shape")
        state[name] = values.reshape(entry["shape"])
    return state


def forward(features, state):
    x = torch.tensor(features, dtype=torch.float32)
    for layer in (0, 2, 4):
        x = F.linear(x, state[f"net.{layer}.weight"], state[f"net.{layer}.bias"])
        if layer != 4:
            x = torch.tanh(x)
    return x.argmax(dim=-1).tolist()


def reason_for(meta, row):
    if meta != META:
        return "YIELD_METADATA"
    if not all(math.isfinite(float(v)) for v in row):
        return "YIELD_NONFINITE"
    dx, dy, vx, vy, confidence, visible = map(float, row)
    if max(abs(dx), abs(dy)) > 1.25 or max(abs(vx), abs(vy)) > 1.0 or not 0 <= confidence <= 1 or visible not in (0., 1.):
        return "YIELD_ENVELOPE"
    if (abs(confidence - .72) < .03 or abs(abs(dx) - .06) < .01 or abs(abs(dy) - .06) < .01
            or abs(abs(vx) + abs(vy) - .12) < .02):
        return "YIELD_BOUNDARY"
    return "PROPOSAL"


def boundary_rows():
    rows = []
    for i in range(256):
        d = .25 + (i % 17) * .001
        rows.extend([[d, .2, .01, .02, .719, 1.], [d, .2, .01, .02, .721, 1.]])
        rows.extend([[.059, 0., .02, .02, .9, 1.], [.061, 0., .02, .02, .9, 1.]])
        rows.extend([[0., 0., .059, .06, .9, 1.], [0., 0., .061, .06, .9, 1.]])
    return torch.tensor(rows, dtype=torch.float32)


def summarize(rows, class_id):
    selected = rows[class_id * 1024:(class_id + 1) * 1024]
    accepted = [row for row in selected if row["proposal"] is not None]
    correct = sum(row["proposal"] == LABELS[row["y"]] for row in accepted)
    correct_class = sum(row["proposal"] == LABELS[class_id] for row in accepted)
    false_correct = sum(row["proposal"] == "CORRECT" and row["y"] != 1 for row in selected)
    return {"n": len(selected), "accepted": len(accepted), "coverage": len(accepted) / 1024,
            "accepted_recall": correct_class / max(1, len(accepted)),
            "accepted_accuracy": correct / max(1, len(accepted)),
            "false_correct": false_correct}


def suite_metrics(rows):
    by_class = {LABELS[c]: summarize(rows, c) for c in range(3)}
    accepted = [row for row in rows if row["proposal"] is not None]
    ncorrect = sum(row["proposal"] == LABELS[row["y"]] for row in accepted)
    false_correct = sum(row["proposal"] == "CORRECT" and row["y"] != 1 for row in rows)
    return {"accepted": len(accepted), "accuracy": ncorrect / max(1, len(accepted)),
            "false_correct": false_correct, "false_correct_fraction_all_rows": false_correct / len(rows),
            "by_class": by_class}


def canonical_result_bytes(raw_bytes):
    """Undo the single Windows checkout's CRLF conversion for Git blob binding."""
    return raw_bytes.replace(b"\r\n", b"\n")


def git_blob_sha1(raw_bytes):
    return hashlib.sha1(b"blob " + str(len(raw_bytes)).encode() + b"\0" + raw_bytes).hexdigest()


def audit(payload, raw_bytes):
    errors = []
    normalized = canonical_result_bytes(raw_bytes)
    if hashlib.sha256(normalized).hexdigest() != EXPECTED_RESULT_SHA256:
        errors.append("formal_result_sha256")
    blob_id = git_blob_sha1(normalized)
    if blob_id != EXPECTED_RESULT_GIT_BLOB:
        errors.append("formal_result_git_blob")
    if payload.get("allocation") != "needle-intent-distill-3458-pilot-06-isolated-shift-audit":
        errors.append("allocation")
    seeds = payload.get("seeds", [])
    if [s.get("seed") for s in seeds] != list(SEEDS):
        return {"audit": "FAIL", "errors": errors + ["seed_set"]}

    reports = []
    all_numeric_gates = []
    for record, seed in zip(seeds, SEEDS):
        where = f"seed_{seed}"
        state_json = json.dumps(record["model_state"], sort_keys=True, separators=(",", ":")).encode()
        if hashlib.sha256(state_json).hexdigest() != record.get("model_state_sha256"):
            errors.append(where + ":model_state_sha256")
        try:
            state = state_tensors(record["model_state"])
        except (KeyError, TypeError, ValueError, RuntimeError):
            errors.append(where + ":model_state_shape")
            continue

        suite_rows = {}
        for suite_name, shifted, offset in (("iid_control", False, 200), ("near_boundary_shift", True, 100)):
            suite = record[suite_name]
            raw_rows = suite.get("rows", [])
            if suite.get("name") != suite_name or len(raw_rows) != 3072:
                errors.append(where + ":" + suite_name + ":row_count_or_name")
                continue
            expected_features = []
            expected_labels = []
            for cls in range(3):
                generator = shifted_class if shifted else balanced_class
                x = generator(cls, 1024, seed + offset + cls)
                expected_features.extend(x.tolist())
                expected_labels.extend(teacher(x).tolist())
            vectors = [row.get("x", []) for row in raw_rows]
            mismatches = [0] * 6
            for row_index, (actual, expected) in enumerate(zip(vectors, expected_features)):
                vector_errors = compare_vector(actual, expected)
                if vector_errors:
                    for error in vector_errors:
                        if error.startswith("feature_"):
                            feature_index = int(error.split("_")[1])
                            mismatches[feature_index] += 1
                    errors.append(f"{where}:{suite_name}:features:{row_index}")
            labels = [row.get("y") for row in raw_rows]
            if labels != expected_labels:
                errors.append(where + ":" + suite_name + ":teacher_labels")
            class_predictions = forward(expected_features, state)
            recalculated_rows = []
            for i, (row, features, label, pred) in enumerate(zip(raw_rows, expected_features, expected_labels, class_predictions)):
                expected_reason = reason_for(META, features)
                expected_proposal = LABELS[pred] if expected_reason == "PROPOSAL" else None
                if row.get("reason") != expected_reason or row.get("proposal") != expected_proposal:
                    errors.append(f"{where}:{suite_name}:decision:{i}")
                recalculated_rows.append({"proposal": expected_proposal, "reason": expected_reason, "y": label})
            suite_rows[suite_name] = recalculated_rows
            if shifted:
                for cls_row in expected_features[1024:2048]:
                    dx, dy, vx, vy, confidence, visible = cls_row
                    if not .071 - 1e-6 <= abs(dx) <= .149 + 1e-6: errors.append(where + ":shift_dx")
                    if abs(dy) > .10 + 1e-6: errors.append(where + ":shift_dy")
                    if abs(vx) > .05 + 1e-6 or abs(vy) > .05 + 1e-6: errors.append(where + ":shift_velocity")
                    if not .80 - 1e-6 <= confidence <= 1.00 + 1e-6: errors.append(where + ":shift_confidence")
                    if visible != 1.0: errors.append(where + ":shift_visibility")
                iid_correct = record["iid_control"]["rows"][1024:2048]
                shifted_correct = raw_rows[1024:2048]
                for iid, shifted_row in zip(iid_correct, shifted_correct):
                    if any(abs(float(a) - float(b)) > 1e-6 for a, b in zip(iid["x"][2:], shifted_row["x"][2:])):
                        errors.append(where + ":shift_changed_nonposition_covariate")
                        break
            summary = suite_metrics(recalculated_rows)
            if suite_name == "near_boundary_shift":
                gates = (summary["accuracy"] >= .95
                         and all(summary["by_class"][LABELS[c]]["coverage"] >= .75
                                 and summary["by_class"][LABELS[c]]["accepted_recall"] >= .95 for c in range(3))
                         and summary["false_correct_fraction_all_rows"] <= .005)
                all_numeric_gates.append(gates)
            suite_rows[suite_name + "_summary"] = summary

        expected_boundary = boundary_rows().tolist()
        actual_boundary = record.get("boundary", [])
        if len(actual_boundary) != 1536:
            errors.append(where + ":boundary_count")
        else:
            for i, (raw, expected) in enumerate(zip(actual_boundary, expected_boundary)):
                if compare_vector(raw.get("x", []), expected): errors.append(f"{where}:boundary_features:{i}")
                if raw.get("reason") != "YIELD_BOUNDARY" or raw.get("proposal") is not None:
                    errors.append(f"{where}:boundary_decision:{i}")

        expected_invalid = [
            ("stale_epoch", META | {"epoch": 8}, [.2, .2, 0., 0., .9, 1.], "YIELD_METADATA"),
            ("wrong_scope", META | {"scope": "other"}, [.2, .2, 0., 0., .9, 1.], "YIELD_METADATA"),
            ("wrong_intent", {"intent": "other", "scope": META["scope"], "epoch": META["epoch"]}, [.2, .2, 0., 0., .9, 1.], "YIELD_METADATA"),
            ("out_of_envelope", META, [1.3, 0., 0., 0., .9, 1.], "YIELD_ENVELOPE"),
            ("nonfinite", META, ["NaN", 0., 0., 0., .9, 1.], "YIELD_NONFINITE"),
        ]
        invalid = record.get("invalid_controls", [])
        if len(invalid) != 5:
            errors.append(where + ":invalid_control_count")
        for actual, (case, meta, expected_x, expected_reason) in zip(invalid, expected_invalid):
            if actual.get("case") != case or actual.get("meta") != meta or actual.get("reason") != expected_reason:
                errors.append(where + ":invalid_control_fields:" + case)
            actual_x = actual.get("x", [])
            for i, (a, e) in enumerate(zip(actual_x, expected_x)):
                if e == "NaN":
                    if a != "NaN": errors.append(where + ":invalid_nan")
                elif abs(float(a) - float(e)) > 1e-6:
                    errors.append(where + f":invalid_feature_{i}")

        latency = record.get("latency_ms", [])
        if len(latency) != 2000 or not all(math.isfinite(float(x)) and float(x) >= 0 for x in latency):
            errors.append(where + ":latency_samples")
        else:
            p95 = sorted(float(x) for x in latency)[int(.95 * (len(latency) - 1))]
            suite_rows["latency_p95_ms"] = p95
            if p95 >= 60:
                errors.append(where + ":latency_gate")
        reports.append({"seed": seed, **suite_rows})

    scientific = "FAIL_NEAR_BOUNDARY_SHIFT" if len(all_numeric_gates) == 3 and not all(all_numeric_gates) else "PASS_OR_INCOMPLETE"
    return {"audit": "PASS" if not errors else "FAIL", "errors": errors,
            "formal_result_sha256": EXPECTED_RESULT_SHA256,
            "formal_result_git_blob_sha1": EXPECTED_RESULT_GIT_BLOB,
            "decision_recomputed": scientific, "seed_numeric_gates": all_numeric_gates,
            "reports": reports, "feature_columns_reconstructed_per_suite_seed": 3072 * 6}


def construction_self_test():
    expected = [.10, -.05, .02, -.01, .90, 1.0]
    for column in range(6):
        changed = expected.copy()
        changed[column] += .01
        assert compare_vector(changed, expected), f"feature mutation not caught: {column}"
    assert compare_vector([.10, -.05, .02, -.01, .90, 1.0], expected) == []
    print(json.dumps({"construction": "PASS", "six_feature_mutations_rejected": 6,
                      "unchanged_vector_passes": True}, sort_keys=True))


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        construction_self_test()
        raise SystemExit(0)
    source = Path(sys.argv[1])
    raw = source.read_bytes()
    payload = json.loads(raw.decode("utf-8"))
    result = audit(payload, raw)
    line = (json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n").encode()
    if "--output" in sys.argv:
        target = Path(sys.argv[sys.argv.index("--output") + 1])
        with target.open("xb") as stream:
            stream.write(line)
    sys.stdout.buffer.write(line)
    if result["audit"] != "PASS":
        raise SystemExit(2)
