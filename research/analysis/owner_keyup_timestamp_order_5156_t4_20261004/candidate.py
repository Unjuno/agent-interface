"""One-shot construction probe of a frozen retained-input analyzer."""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path


def load_module(path):
    spec = importlib.util.spec_from_file_location("frozen_analyzer", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    cases_path, source_path, output_path = map(Path, sys.argv[1:4])
    cases = json.loads(cases_path.read_text(encoding="utf-8"))
    source_bytes = source_path.read_bytes()
    analyzer = load_module(source_path)
    rows = []
    for case in cases["cases"]:
        events = [
            {"event":"input_admission", "intent_token":"frozen-intent", "key":"Up",
             "admitted_ns":case["admitted_ns"], "input_ack_ns":case["input_ack_ns"]},
            {"event":"input_release_transition", "intent_token":"frozen-intent",
             "operation":"up", "key":"Up",
             "release_call_started_ns":case["release_call_started_ns"],
             "release_call_returned_ns":case["release_call_returned_ns"],
             "owner_transition_verified":True},
        ]
        rows.append({"case_id":case["id"], "events":events,
                     "analyzer_output":analyzer.analyze(events)})
    result = {"schema":"owner-keyup-timestamp-order-raw-v1",
              "allocation":cases["allocation"],
              "analyzer_sha256":hashlib.sha256(source_bytes).hexdigest(),
              "python":sys.version.split()[0], "rows":rows}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    print(json.dumps({"allocation":result["allocation"], "row_count":len(rows),
                      "measurement_ready":[r["analyzer_output"]["measurement_ready"] for r in rows]},
                     sort_keys=True))


if __name__ == "__main__":
    main()
