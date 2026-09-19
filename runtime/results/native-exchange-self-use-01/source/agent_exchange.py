"""Agent-facing composition of own-clock validation and prepared v27 input.

Explicit actions only, one clock and at most one submit, with no retry.
Frozen component sources remain unchanged.
"""
import argparse
import copy
import json
import math
import os
from pathlib import Path
import sys
import time
import uuid

from early_exchange_v1 import own_command, prefix
from drain_final import drain_final
from outcome_wait import interpret
from prepare_program import prepare
from receipt_image import select_image
from unix_json_deadline import exchange


def run(socket_path, batch, run_directory, program_id, steps, *, out,
        lease_ms=5000, boundary="terminal", timeout=5, transport=exchange):
    """Preserve reviewed image identity while acquiring a correlated clock."""
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)

    def persist(name, value):
        with (out / (name + ".json")).open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(value, indent=2, allow_nan=False) + "\n")
            stream.flush()
            os.fsync(stream.fileno())

    result = {"status": "needs_review", "program_id": program_id, "program_attempted": False,
              "authority": "none", "records": [], "exchanges": [], "started_ns": time.perf_counter_ns()}

    def call(name, request, *, transport_timeout=None):
        persist(name + "-request", request)
        entry = {"request": str(out / (name + "-request.json")), "started_ns": time.perf_counter_ns()}
        result["exchanges"].append(entry)
        if name == "program":
            result["program_attempted"] = True
        reply = transport(socket_path, request, timeout=timeout + 1 if transport_timeout is None else transport_timeout)
        entry["returned_ns"] = time.perf_counter_ns()
        persist(name + "-reply", reply)
        entry["reply"] = str(out / (name + "-reply.json"))
        return reply

    try:
        if type(timeout) not in (int, float) or not math.isfinite(timeout) or not 0 <= timeout <= 30:
            raise ValueError("timeout 0..30 required")
        if boundary not in ("terminal", "outcome"):
            raise ValueError("terminal or outcome boundary required")
        if type(lease_ms) is not int or not 1 <= lease_ms <= 30000:
            raise ValueError("lease_ms 1..30000 required")
        if not isinstance(program_id, str) or not 1 <= len(program_id) <= 128:
            raise ValueError("bounded explicit program ID required")
        if not isinstance(steps, list) or not steps:
            raise ValueError("explicit steps required")
        batch = json.loads(json.dumps(batch, allow_nan=False))
        steps = json.loads(json.dumps(steps, allow_nan=False))
        if type(batch.get("cursor")) is not int or batch["cursor"] < 0:
            raise ValueError("received cursor required")
        source = select_image(batch, run_directory)
        if source["status"] != "image":
            raise ValueError("received image required")
        persist("source-batch", batch)
        persist("steps", steps)
        result["source_image"] = source
        clock_id = "clock:" + uuid.uuid4().hex
        request = {"after": batch["cursor"], "events": ["clock"], "timeout": min(timeout, 5),
                   "request_id": clock_id, "command": {"op": "clock"}}
        clock = call("clock", request)
        rows = prefix(clock, batch["cursor"])
        index = own_command(rows, clock_id, "clock")
        if len(rows) != 2 or index != 0 or rows[-1].get("event") != "clock":
            raise ValueError("intervening events require review before input")
        if rows[0].get("command") != {"op": "clock", "transport_request_id": clock_id}:
            raise ValueError("clock echo does not match request")
        now = rows[-1]
        if (type(now.get("sequence")) is not int or now["sequence"] != source["sequence"] or
                type(now.get("runtime_ns")) is not int or now["runtime_ns"] <= 0):
            raise ValueError("clock/image mismatch; clock does not refresh the image")
        combined = copy.deepcopy(batch)
        combined["records"] += rows
        combined["cursor"] = clock["cursor"]
        prepared = prepare(combined, run_directory, program_id, steps,
                           lease_ms=lease_ms, finish_after=boundary == "outcome")
        persist("preparation", prepared)
        identifier = "program:" + uuid.uuid4().hex
        result["request_id"] = identifier
        reply = call("program", {"after": clock["cursor"],
                     "events": ["terminal"] if boundary == "terminal" else ["effect_evidence", "independent_evaluation"],
                     "timeout": timeout, "request_id": identifier, "read_request_id": identifier,
                     "command": prepared["command"]})
        if reply.get("status") == "error":
            raise ValueError("server rejected request: " + str(reply.get("message", reply.get("error"))))
        result.update(status=reply["status"], cursor=reply.get("cursor"),
                      command_receipt=reply.get("command_receipt"), records=reply.get("records", []))
        if boundary == "outcome":
            result["outcome"] = interpret(reply, identifier)
            def read_final(spec):
                tail = call('final', spec, transport_timeout=.25)
                rows = tail.get('records')
                if (not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows)
                        or type(tail.get('cursor')) is not int
                        or tail['cursor'] != spec['after'] + len(rows)):
                    raise ValueError('final read is not a contiguous received prefix')
                return tail
            result['drain'] = drain_final(read_final, result['outcome'], identifier, program_id)
            result['outcome'] = result['drain']['outcome']
            if 'reply' in result['drain']:
                result['records'] = result['records'] + result['drain']['reply']['records']
                result['cursor'] = result['drain']['reply']['cursor']
        try:
            result["image"] = select_image(result, run_directory)
        except Exception as error:
            result["image_error"] = str(error)
    except Exception as error:
        result.update(status="needs_review", error=str(error),
                      recovery="Inspect saved requests and replies. Do not replay input; use command-free reads to reconcile uncertainty.")
    result["returned_ns"] = time.perf_counter_ns()
    persist("report", result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", default="-", help="one JSON request; '-' reads stdin")
    parser.add_argument("--review", nargs="?", const="full", choices=("full", "compact"), help="return receipt and image together after the one action attempt")
    parser.add_argument("--native", action="store_true", help="submit/wait/review one private native harness stage")
    args = parser.parse_args()
    try:
        raw = json.loads(sys.stdin.read() if args.request == "-" else Path(args.request).read_text())
        if args.native:
            if args.review == "compact":
                raise ValueError("compact native review is not supported")
            from native_exchange_v1 import run as native_run
            displayed = native_run(**raw)
            print(json.dumps(displayed), flush=True)
            return 0
        request = resolve_request(raw)
        result = run(**request)
    except Exception as error:
        # Artifact persistence itself may fail after a write attempt. Do not
        # manufacture a no-input verdict when no complete report is available.
        print(json.dumps({"status": "client_error", "error": str(error), "program_attempted": None,
                          "recovery": "Inspect any existing artifacts; input outcome is not inferred."}))
        return 2
    displayed = result
    if args.review:
        try:
            from agent_review import review
            displayed = review(Path(request['out']) / 'report.json', request['run_directory'], compact=args.review == 'compact')
        except Exception as error:
            # Rendering/preparation is after input. Retain the result without retry.
            displayed = {"report": result, "review_error": str(error), "image": None}
    print(json.dumps(displayed), flush=True)
    return 2 if result["status"] == "needs_review" else 0


def resolve_request(request):
    """Load exactly the caller-selected full batch; never infer a latest file."""
    if not isinstance(request, dict):
        raise ValueError('request object required')
    request = dict(request)
    if 'batch_file' in request:
        if 'batch' in request:
            raise ValueError('provide batch or batch_file, not both')
        path = request.pop('batch_file')
        if not isinstance(path, str) or not path:
            raise ValueError('explicit batch_file path required')
        batch = json.loads(Path(path).read_text(encoding='utf-8'))
        if (not isinstance(batch, dict) or type(batch.get('cursor')) is not int
                or batch['cursor'] < 0 or not isinstance(batch.get('records'), list)):
            raise ValueError('batch_file must contain a full received batch/report, not a presentation view')
        request['batch'] = batch
    return request


if __name__ == "__main__":
    raise SystemExit(main())
