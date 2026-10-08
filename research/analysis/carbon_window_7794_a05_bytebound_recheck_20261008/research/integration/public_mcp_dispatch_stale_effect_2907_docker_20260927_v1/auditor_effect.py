"""Independent raw-only gate for a single public MCP stale/effect run."""
import copy
import base64
import hashlib
import json
from pathlib import Path


EXPECTED = ["01-observe-seq1", "02-observe-seq2", "03-stale-dispatch",
            "04-fresh-dispatch", "05-post-effect-observe", "06-close"]


def errors(bundle):
    out = []
    trace = bundle.get("trace", {})
    result = bundle.get("result", {})
    calls = trace.get("calls", [])
    by_label = {row.get("label"): row for row in calls}
    if [row.get("label") for row in calls] != EXPECTED:
        out.append("call-order-or-count")
    if result.get("decision") != "PASS_PUBLIC_MCP_STALE_EFFECT_RELEASE_SCOPED":
        out.append("formal-decision")
    if len(calls) != len(EXPECTED):
        return out + ["missing-call"]
    if len({row.get("payload", {}).get("session", {}).get("session_id") for row in calls}) != 1:
        out.append("session-divergence")
    if not trace.get("session_id") or any(
            row.get("payload", {}).get("session", {}).get("session_id") != trace.get("session_id")
            for row in calls):
        out.append("session-binding")

    stale = by_label.get("03-stale-dispatch", {}).get("raw_report", {}).get("result", {})
    gate = trace.get("stale_gate", {})
    if (stale.get("status") != "refused" or stale.get("error") != "STALE_OBSERVATION"
            or stale.get("backend_emissions") != 0 or gate.get("program_source_sequence") != 1
            or gate.get("caller_current_sequence") != 2):
        out.append("stale-refusal")

    action = by_label.get("04-fresh-dispatch", {}).get("raw_report", {}).get("result", {})
    execution = action.get("execution", {})
    releases = execution.get("releases", [])
    if action.get("status") != "completed" or type(execution.get("program_emissions")) is not int or execution.get("program_emissions", 0) <= 0:
        out.append("fresh-action")
    if not releases or any(not isinstance(row, dict) or row.get("verified") is not True
                           or row.get("keys_down") != [] or row.get("buttons_down") != []
                           for row in releases):
        out.append("action-release")

    effect = trace.get("effect_receipt", {})
    identities = bundle.get("app_identities", [])
    chrome = next((row for row in identities if row.get("name") == "chromium"), {})
    if (effect.get("matched") is not True or effect.get("marker") not in effect.get("wm_name", "")
            or effect.get("window_id") != chrome.get("window_id")):
        out.append("independent-effect")

    close = by_label.get("06-close", {}).get("raw_report", {})
    if close.get("status") != "closed" or close.get("release_attempted") is not True:
        out.append("close-release")
    result_close = result.get("close", {})
    if result_close.get("session_id") != trace.get("session_id"):
        out.append("close-session")
    retained = trace.get("retained_reads", [])
    if (len(retained) != len(EXPECTED) or any(row.get("state") != "finished"
            or row.get("operation_invoked") is not False or row.get("session_id") != trace.get("session_id")
            for row in retained)):
        out.append("retained-reads")
    if result.get("x_socket_absent") is not True or result.get("server_processes_after_shutdown") != []:
        out.append("cleanup")
    if any(row.get("still_running_pids") for row in result.get("cleanup", [])):
        out.append("live-owned-process")
    bundle_path = Path(bundle.get("bundle_path", ""))
    raw_responses_valid = True
    for call in calls:
        response_path = bundle_path / "mcp-responses" / call.get("response_file", "")
        try:
            raw_bytes = response_path.read_bytes()
            raw_json = json.loads(raw_bytes)
            if hashlib.sha256(raw_bytes).hexdigest() != call.get("response_metadata", {}).get("response_sha256"):
                raw_responses_valid = False
                continue
            blocks = raw_json.get("content", [])
            text_blocks = [row.get("text") for row in blocks if row.get("type") == "text"]
            if len(text_blocks) != 1 or json.loads(text_blocks[0]) != call.get("payload"):
                raw_responses_valid = False
                continue
            image_blocks = [row for row in blocks if row.get("type") == "image"]
            image_meta = [row for row in call.get("response_metadata", {}).get("blocks", [])
                          if row.get("type") == "image"]
            if len(image_blocks) != len(image_meta):
                raw_responses_valid = False
                continue
            for image, meta in zip(image_blocks, image_meta):
                image_bytes = base64.b64decode(image.get("data", ""), validate=True)
                image_path = bundle_path / "mcp-responses" / "images" / Path(meta.get("path", "")).name
                if (hashlib.sha256(image_bytes).hexdigest() != meta.get("sha256")
                        or image_path.read_bytes() != image_bytes):
                    raw_responses_valid = False
        except (OSError, ValueError, TypeError):
            raw_responses_valid = False
    if not raw_responses_valid:
        out.append("raw-response-byte-binding")
    if result.get("model_calls") != 0 or result.get("network_calls") != 0 or result.get("authority_granted") is not False:
        out.append("scope-counters")
    return out


def audit(bundle):
    controls = {}
    for name, mutate in [
        ("stale-error", lambda b: b["trace"]["calls"][2]["raw_report"]["result"].update(error="none")),
        ("wrong-effect", lambda b: b["trace"]["effect_receipt"].update(matched=False)),
        ("unverified-release", lambda b: b["trace"]["calls"][3]["raw_report"]["result"]["execution"]["releases"][0].update(verified=False)),
        ("session-split", lambda b: b["trace"]["calls"][1]["payload"]["session"].update(session_id="mutated")),
        ("drop-retained-read", lambda b: b["trace"]["retained_reads"].pop()),
    ]:
        candidate = copy.deepcopy(bundle)
        mutate(candidate)
        controls[name] = bool(errors(candidate))
    problems = errors(bundle)
    return {"decision": "PASS_RAW_AUDIT" if not problems and all(controls.values()) else "HOLD_RAW_AUDIT",
            "errors": problems, "corruption_controls_rejected": controls,
            "corruption_control_count": len(controls),
            "formal_decision": bundle.get("result", {}).get("decision"),
            "scope": "independent raw-only reconstruction; no MCP calls or input"}


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    bundle_path = Path(args.bundle)
    bundle = {
        "trace": json.loads((bundle_path / "trace.json").read_text(encoding="utf-8")),
        "result": json.loads((bundle_path / "result.json").read_text(encoding="utf-8")),
        "app_identities": json.loads((bundle_path / "app-identities.json").read_text(encoding="utf-8")),
        "bundle_path": str(bundle_path),
    }
    report = audit(bundle)
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=False)
    raw = json.dumps(report, sort_keys=True, indent=2).encode() + b"\n"
    (output / "audit.json").write_bytes(raw)
    import hashlib
    (output / "sha256.txt").write_text(hashlib.sha256(raw).hexdigest() + "  audit.json\n")
    print(json.dumps(report, sort_keys=True))
    return 0 if report["decision"] == "PASS_RAW_AUDIT" else 1


if __name__ == "__main__":
    raise SystemExit(main())
