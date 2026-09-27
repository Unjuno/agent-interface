"""Independent raw/result audit; intentionally imports no experiment code."""
import base64
import hashlib
import json
from pathlib import Path
import struct
import zlib


def sha(data):
    return hashlib.sha256(data).hexdigest()


def png_valid(data):
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        return False
    offset, idat, header, ended = 8, bytearray(), None, False
    while offset < len(data):
        if offset + 12 > len(data):
            return False
        length = struct.unpack(">I", data[offset:offset + 4])[0]
        kind = data[offset + 4:offset + 8]
        payload = data[offset + 8:offset + 8 + length]
        if len(payload) != length:
            return False
        crc = struct.unpack(">I", data[offset + 8 + length:offset + 12 + length])[0]
        if zlib.crc32(kind + payload) & 0xffffffff != crc:
            return False
        if kind == b"IHDR":
            if len(payload) != 13:
                return False
            header = struct.unpack(">IIBBBBB", payload)
        elif kind == b"IDAT":
            idat.extend(payload)
        elif kind == b"IEND":
            ended = True
            offset += length + 12
            break
        offset += length + 12
    if not ended or offset != len(data) or header is None:
        return False
    width, height, depth, color_type, compression, filt, interlace = header
    channels = {0: 1, 2: 3, 4: 2, 6: 4}.get(color_type)
    if not width or not height or depth != 8 or channels != 3 or compression or filt or interlace:
        return False
    try:
        raw = zlib.decompress(idat)
    except zlib.error:
        return False
    stride = width * channels
    return len(raw) == height * (stride + 1) and all(raw[y * (stride + 1)] == 0 for y in range(height))


def badge_color(data):
    offset, idat = 8, bytearray()
    while offset + 12 <= len(data):
        n = struct.unpack(">I", data[offset:offset + 4])[0]
        kind, payload = data[offset + 4:offset + 8], data[offset + 8:offset + 8 + n]
        offset += n + 12
        if kind == b"IDAT":
            idat.extend(payload)
        if kind == b"IEND":
            break
    raw = zlib.decompress(idat)
    width, height, channels = 448, 280, 3
    stride = width * channels + 1
    pixel = tuple(raw[140 * stride + 1 + 224 * channels:140 * stride + 1 + 225 * channels])
    return "green" if pixel == (25, 153, 78) else "red" if pixel == (205, 47, 54) else "unknown"


def expected_decision(scenario, policy, max_skew):
    rows = [{"channel": "image", **scenario["image"]}, *scenario["channels"]]
    epochs, tasks = {r["epoch"] for r in rows}, {r["task_id"] for r in rows}
    captures = [r["capture_ms"] for r in rows]
    skew = max(captures) - min(captures)
    duplicate = len({r["channel"] for r in rows}) != len(rows)
    if policy == "TYPED_EPOCH_AWARE_COMPOSER":
        if len(epochs) != 1 or len(tasks) != 1 or duplicate or skew > max_skew:
            return "ABSTAIN_BEFORE_MODEL", []
        return ("COMPOSE_SKEWED_CONTEXT" if skew else "COMPOSE_COHERENT"), rows
    if policy == "EPOCH_REJECT_ONLY":
        if len(epochs) != 1 or len(tasks) != 1 or duplicate or skew != 0:
            return "ABSTAIN_BEFORE_MODEL", []
        return "COMPOSE_COHERENT", rows
    if policy == "BEST_EFFORT_MERGE":
        return "COMPOSE_ALL_AVAILABLE", rows
    if policy == "LATEST_CHANNEL_WINS":
        latest = {}
        for row in rows:
            if row["channel"] not in latest or row["arrival_ms"] > latest[row["channel"]]["arrival_ms"]:
                latest[row["channel"]] = row
        return "COMPOSE_LATEST_PER_CHANNEL", list(latest.values())
    return "UNKNOWN_POLICY", []


def expected_prompt(scenario_id, policy, bundle, skew):
    records = [{k: v for k, v in row.items() if k != "color"} for row in bundle]
    return ("You are a narrow visual status reader. The screenshot has a large badge: green means READY; red means BLOCKED. "
            "Requested target task-A. Use task_id, epoch, capture_ms and arrival_ms. If records conflict across epochs, "
            "contain duplicate state channels, or cannot support one current status, return ABSTAIN. Otherwise return "
            'the status supported by coherent evidence. Return only JSON {"answer":"READY"|"BLOCKED"|"ABSTAIN"}.\n'
            f"Scenario={scenario_id}; policy={policy}; measured_capture_skew_ms={skew}; "
            f"channels={json.dumps(records, sort_keys=True, separators=(',', ':'))}")


def main():
    root, output = Path("/audit"), Path("/out")
    freeze = json.loads((root / "FREEZE.json").read_text())
    manifest = json.loads((root / "manifest.json").read_text())
    result = json.loads((root / "RESULT.json").read_text())
    bridge = json.loads((root / "BRIDGE_SUMMARY.json").read_text())
    rpc = root / "exchange"
    checks = {
        "formal_mode": result.get("run_mode") == "FORMAL",
        "allocation": result.get("allocation") == manifest["allocation"] == freeze["allocation"],
        "base_commit": result.get("base_commit") == freeze["base_commit"],
        "prereg_hash": result.get("preregistration_sha256") == freeze["preregistration_sha256"] == sha((root / "PREREGISTRATION.md").read_bytes()),
        "freeze_hash": result.get("freeze_sha256") == sha((root / "FREEZE.json").read_bytes()),
        "source_hashes": all(sha((root / name).read_bytes()) == expected for name, expected in freeze["sha256"].items()),
        "source_checks": all(result.get("source_checks", {}).values()) and set(result.get("source_checks", {})) == set(freeze["sha256"]),
        "obstac_source": result.get("obstac_environment", {}).get("OBSTAC_SOURCE_COMMIT") == freeze["base_commit"],
        "obstac_image": result.get("obstac_environment", {}).get("OBSTAC_IMAGE_ID") == freeze["image_id"],
        "obstac_freeze": result.get("obstac_environment", {}).get("OBSTAC_FREEZE_SHA256") == result.get("freeze_sha256"),
        "bridge_identity": bridge.get("mode") == "LOCAL_OLLAMA" and bridge.get("digest") == freeze["model_digest"] and bridge.get("initial_model_digest") == freeze["model_digest"] == bridge.get("final_model_digest"),
        "action_free": result.get("action_calls") == 0 and result.get("effect_claims") == 0,
        "no_stop": result.get("stop") is None and bridge.get("stop") is None,
    }
    if result.get("stop") is not None or bridge.get("stop") is not None or len(result.get("rows", [])) != 12:
        rpc = root / "exchange"
        requests = sorted(rpc.glob("request-*.json"))
        responses = sorted(rpc.glob("response-*.json"))
        receipts = {r.get("call_id"): r for r in bridge.get("receipts", [])}
        bound = all(checks[k] for k in ("formal_mode", "allocation", "base_commit", "prereg_hash", "freeze_hash",
                                        "source_hashes", "source_checks", "obstac_source", "obstac_image", "obstac_freeze"))
        bound &= len(requests) == len(responses) == len(receipts) and len(requests) <= 9
        retained_error = False
        for req_path in requests:
            call_id = req_path.stem.removeprefix("request-")
            res_path = rpc / f"response-{call_id}.json"
            if not res_path.exists():
                bound = False
                continue
            req_bytes, res_bytes = req_path.read_bytes(), res_path.read_bytes()
            req, res = json.loads(req_bytes), json.loads(res_bytes)
            receipt = receipts.get(call_id, {})
            raw = base64.b64decode(res.get("raw_body_base64", ""), validate=True)
            bound &= receipt.get("request_sha256") == sha(req_bytes) and receipt.get("response_sha256") == sha(res_bytes)
            bound &= sha(raw) == res.get("raw_body_sha256")
            if res.get("status") == "HTTP_ERROR":
                retained_error = res.get("http_status") is not None and bool(raw)
            if req.get("format") != "json" or req.get("model_digest") != freeze["model_digest"]:
                bound = False
        partial = {"audit_version": "independent-v3", "gate": "STOP_FORMAL_EVIDENCE_RETAINED" if bound else "STOP_EVIDENCE_INTEGRITY_UNCONFIRMED",
                   "checks": {**checks, "partial_request_response_receipts": bool(bound), "exact_http_error_retained": retained_error,
                              "formal_stop_reason": result.get("stop") or bridge.get("stop") or "INCOMPLETE_GRID"},
                   "scope": "partial formal allocation; no efficacy decision"}
        (output / "AUDIT.json").write_text(json.dumps(partial, indent=2, sort_keys=True) + "\n")
        print(json.dumps(partial, sort_keys=True))
        raise SystemExit(0 if bound else 2)
    keyed = {(row.get("scenario"), row.get("policy")): row for row in result.get("rows", [])}
    expected_keys = {(s["id"], p) for s in manifest["scenarios"] for p in manifest["policies"]}
    checks["full_unique_grid"] = len(keyed) == 12 and set(keyed) == expected_keys and result.get("scenario_count") == 3 and result.get("policy_count") == 4
    requests = sorted(rpc.glob("request-*.json"))
    responses = sorted(rpc.glob("response-*.json"))
    receipts = {r.get("call_id"): r for r in bridge.get("receipts", [])}
    checks["call_budget"] = result.get("model_calls") == bridge.get("calls_submitted") == 9 and len(requests) == len(responses) == len(receipts) == 9
    calls_ok, image_ok, identity_ok, policy_ok = True, True, True, True
    for scenario in manifest["scenarios"]:
        image_path = root / "images" / f"{scenario['id']}.png"
        image_bytes = image_path.read_bytes()
        image_ok &= png_valid(image_bytes) and badge_color(image_bytes) == scenario["image"]["color"]
        image_sha = sha(image_bytes)
        for policy in manifest["policies"]:
            row = keyed.get((scenario["id"], policy), {})
            image_ok &= row.get("image_sha256") == image_sha and row.get("expected") == scenario["expected"]
            disposition, bundle = expected_decision(scenario, policy, manifest["max_skew_ms"])
            policy_ok &= row.get("disposition") == disposition and row.get("input_epoch_set") == sorted({r["epoch"] for r in [{"channel": "image", **scenario["image"]}, *scenario["channels"]]})
            if disposition == "ABSTAIN_BEFORE_MODEL":
                policy_ok &= row.get("model_called") is False and row.get("answer") == "ABSTAIN"
            else:
                policy_ok &= row.get("model_called") is True
            if row.get("model_called"):
                call_id = row.get("call_id")
                req_path, res_path = rpc / f"request-{call_id}.json", rpc / f"response-{call_id}.json"
                req_bytes, res_bytes = req_path.read_bytes(), res_path.read_bytes()
                req, res = json.loads(req_bytes), json.loads(res_bytes)
                rec = receipts.get(call_id, {})
                image_in_req = base64.b64decode(req.get("image_png_base64", ""), validate=True)
                calls_ok &= rec.get("request_sha256") == sha(req_bytes) and rec.get("response_sha256") == sha(res_bytes)
                calls_ok &= row.get("request_sha256") == sha(req_bytes) and row.get("response") == res
                calls_ok &= req.get("call_id") == call_id and req.get("format") == "json" and req.get("prompt_sha256") == sha(req["prompt"].encode())
                calls_ok &= sha(image_in_req) == req.get("image_sha256") == row.get("image_sha256") == image_sha
                calls_ok &= req.get("model_digest") == freeze["model_digest"] and res.get("status") == "OK" and res.get("http_status") == 200
                calls_ok &= req.get("format") == "json" and req.get("options") == freeze["options"]
                calls_ok &= req.get("prompt") == expected_prompt(scenario["id"], policy, bundle, row.get("measured_capture_skew_ms"))
                raw = base64.b64decode(res.get("raw_body_base64", ""), validate=True)
                calls_ok &= sha(raw) == res.get("raw_body_sha256")
                body = json.loads(raw)
                calls_ok &= body == res.get("ollama_response") and body.get("model") == freeze["model"]
                api_raw = base64.b64decode(res.get("request_body_base64", ""), validate=True)
                calls_ok &= sha(api_raw) == res.get("request_body_sha256")
                api = json.loads(api_raw)
                calls_ok &= api.get("model") == freeze["model"] and api.get("format") == "json" and api.get("options") == freeze["options"]
                calls_ok &= api.get("stream") is False and api.get("messages") == [{"role": "user", "content": req["prompt"], "images": [req["image_png_base64"]]}]
                identity_ok &= res.get("model_digest") == freeze["model_digest"]
            else:
                calls_ok &= row.get("answer") == "ABSTAIN" and row.get("disposition") == "ABSTAIN_BEFORE_MODEL"
    checks["rpc_byte_links"] = bool(calls_ok)
    checks["png_crc_filter_scanlines"] = bool(image_ok)
    checks["per_call_model_identity"] = bool(identity_ok)
    checks["independent_policy_reconstruction"] = bool(policy_ok)
    candidate = [keyed.get((s["id"], "TYPED_EPOCH_AWARE_COMPOSER"), {}) for s in manifest["scenarios"]]
    rejector = [keyed.get((s["id"], "EPOCH_REJECT_ONLY"), {}) for s in manifest["scenarios"]]
    checks["candidate_exact"] = all(r.get("answer") == s["expected"] for r, s in zip(candidate, manifest["scenarios"]))
    checks["candidate_conflict_preabstain"] = keyed.get(("cross_epoch_conflict", "TYPED_EPOCH_AWARE_COMPOSER"), {}).get("model_called") is False
    checks["candidate_more_coverage"] = sum(r.get("answer") == s["expected"] for r, s in zip(candidate, manifest["scenarios"])) > sum(r.get("answer") == s["expected"] for r, s in zip(rejector, manifest["scenarios"]))
    mutated_answer = dict(keyed.get(("aligned", "TYPED_EPOCH_AWARE_COMPOSER"), {}), answer="CORRUPTED")
    mutated_conflict = dict(keyed.get(("cross_epoch_conflict", "TYPED_EPOCH_AWARE_COMPOSER"), {}), model_called=True)
    checks["corruption_controls"] = mutated_answer.get("answer") != "READY" and mutated_conflict.get("model_called") is not False
    integrity_keys = ("formal_mode", "allocation", "base_commit", "prereg_hash", "freeze_hash", "source_hashes", "source_checks",
                      "obstac_source", "obstac_image", "obstac_freeze", "bridge_identity", "action_free", "no_stop",
                      "full_unique_grid", "call_budget", "rpc_byte_links", "png_crc_filter_scanlines", "per_call_model_identity", "corruption_controls")
    integrity_keys = (*integrity_keys, "independent_policy_reconstruction")
    integrity = all(checks[k] for k in integrity_keys)
    if not integrity:
        gate = "STOP_EVIDENCE_OR_PROVENANCE_INVALID"
    elif not checks["candidate_exact"] or not checks["candidate_conflict_preabstain"]:
        gate = "FAIL_MODEL_FACING_EPOCH_COMPOSITION_SCOPED"
    elif not checks["candidate_more_coverage"]:
        gate = "HOLD_NO_USEFUL_COVERAGE_GAIN"
    else:
        gate = "PASS_MODEL_FACING_EPOCH_COMPOSITION_SCOPED"
    audit = {"audit_version": "independent-v3", "gate": gate, "checks": checks,
             "candidate_answers": [r.get("answer") for r in candidate], "reject_only_answers": [r.get("answer") for r in rejector]}
    (output / "AUDIT.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    print(json.dumps(audit, sort_keys=True))
    raise SystemExit(0 if gate.startswith("PASS_") else 2)


if __name__ == "__main__":
    main()
