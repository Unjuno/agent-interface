"""Independent raw-only audit for Issue #3876 live-producer reader evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def need(errors: list[str], condition: bool, name: str) -> None:
    if not condition:
        errors.append(name)


def json_lines(path: Path) -> tuple[bytes, list[dict]]:
    data = path.read_bytes()
    rows = [json.loads(line) for line in data.splitlines()]
    return data, rows


def audit(repo: Path, run: Path, freeze_path: Path) -> dict:
    errors: list[str] = []
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    run_result = json.loads((run / "runner_result.json").read_text(encoding="utf-8"))
    run_record = json.loads((run / "run.json").read_text(encoding="utf-8"))
    delivered_bytes, delivered = json_lines(run / "producer" / "delivered.jsonl")
    event_bytes, events = json_lines(run / "producer" / "events.jsonl")
    flush_bytes, flushes = json_lines(run / "producer" / "delivery-flush.jsonl")
    stdout_bytes = (run / "producer_stdout.jsonl").read_bytes()
    stdout_rows = [json.loads(line) for line in stdout_bytes.splitlines()]
    reader_responses = []
    reader_meta = []
    for label in ("reader1", "reader2", "reader3"):
        payload = (run / f"{label}_stdout.bin").read_bytes()
        response = json.loads(payload)
        meta = json.loads((run / f"{label}_meta.json").read_text(encoding="utf-8"))
        need(errors, meta["returncode"] == 0 and (run / f"{label}_stderr.bin").read_bytes() == b"",
             f"{label}:process")
        reader_responses.append(response)
        reader_meta.append(meta)

    need(errors, freeze.get("schema") == "issue-3876-live-reader-freeze-v1", "freeze:schema")
    need(errors, freeze.get("allocation") == "issue-3876-live-reader-20260921-01", "freeze:allocation")
    need(errors, freeze.get("base_image_id") ==
         "sha256:eaf46582f96fd46a1ad6a240928b4c2a828de3d058a4b1490bbadf708d5a52d3",
         "freeze:base-image")
    need(errors, (run / "freeze.json").read_bytes() == freeze_path.read_bytes(), "freeze:retained-copy")
    need(errors, run_result.get("status") == "RUN_COMPLETED", "runner:status")
    need(errors, run_result.get("producer_returncode") == 0, "producer:exit")
    need(errors, run_record.get("returncode") == 0, "run:producer-exit")
    need(errors, run_record.get("image_id") == freeze["image_id"], "image:identity")
    need(errors, run_result.get("image_id") == freeze["image_id"], "runner:image-identity")
    need(errors, run_result.get("stream_id") == run_record.get("stream_id"), "stream:runner-run-binding")
    need(errors, run_result.get("stream_id") == run_record.get("stream_id"), "stream:runner-run-binding")

    actual_freeze_hashes = {}
    for name, expected in freeze["inputs"].items():
        actual = sha256((repo / name).read_bytes())
        actual_freeze_hashes[name] = actual
        need(errors, actual == expected, f"freeze:source:{name}")
    producer_sources = run_record.get("source_manifest", {})
    for name in producer_sources:
        key = "research/" + name
        need(errors, key in freeze["inputs"] and producer_sources[name] == freeze["inputs"].get(key),
             f"producer:source-binding:{name}")
    need(errors, len(producer_sources) >= 25, "producer:source-manifest-size")

    sum_lines = (run / "SHA256SUMS").read_text(encoding="utf-8").splitlines()
    manifest = {}
    for line in sum_lines:
        digest, name = line.split("  ", 1)
        manifest[name] = digest
    for path in sorted(p for p in run.rglob("*") if p.is_file() and p.name != "SHA256SUMS"):
        name = path.relative_to(run).as_posix()
        need(errors, manifest.get(name) == sha256(path.read_bytes()), f"run:sha256:{name}")
    need(errors, set(manifest) == {p.relative_to(run).as_posix()
         for p in run.rglob("*") if p.is_file() and p.name != "SHA256SUMS"}, "run:manifest-set")

    need(errors, stdout_bytes == delivered_bytes, "producer:stdout-delivered-byte-equality")
    need(errors, len(stdout_rows) == len(delivered) == len(events) == len(flushes), "producer:row-counts")
    for index, (raw, visible, event, receipt) in enumerate(zip(stdout_rows, delivered, events, flushes), 1):
        need(errors, raw == visible, f"producer:stdout-row:{index}")
        without_id = dict(visible)
        delivery_id = without_id.pop("delivery_id", None)
        need(errors, delivery_id == f"delivery:{index}", f"producer:delivery-id:{index}")
        need(errors, without_id == event, f"producer:logical-visible-row:{index}")
        need(errors, receipt.get("event") == "delivery_flush" and
             receipt.get("delivery_id") == delivery_id and
             receipt.get("utf8_bytes") == len(delivered_bytes.splitlines(keepends=True)[index - 1]),
             f"producer:flush-receipt:{index}")

    first, second, third = reader_responses
    need(errors, run_record.get("live_reader_producer_alive") is True, "reader1:producer-live")
    need(errors, [row.get("event") for row in first.get("records", [])] ==
         ["ready", "observation", "command", "clock"], "reader1:event-sequence")
    need(errors, [row.get("event") for row in second.get("records", [])] ==
         ["command", "independent_evaluation"], "reader2:event-sequence")
    need(errors, third.get("records") == [] and third.get("tail_state") == "end",
         "reader3:empty-end")
    need(errors, first.get("records", []) + second.get("records", []) == delivered,
         "reader:complete-content-order")
    for index, response in enumerate(reader_responses, 1):
        need(errors, response.get("authority") == "none" and response.get("acknowledged") is False and
             response.get("input_dispatched") is False, f"reader{index}:non-authority")
        need(errors, response.get("schema") == "agent-interface/experimental-inbox-read-v1" and
             response.get("problem") is None, f"reader{index}:schema-problem")
        need(errors, response.get("next_cursor", {}).get("stream_id") == run_result.get("stream_id"),
             f"reader{index}:stream-id")
    cursor_rows = []
    for index, response in enumerate(reader_responses, 1):
        cursor = json.loads((run / f"reader{index}_cursor.json").read_text(encoding="utf-8"))
        cursor_rows.append(cursor)
        need(errors, cursor == response["next_cursor"], f"reader{index}:saved-cursor")
    prefix1 = b"".join(delivered_bytes.splitlines(keepends=True)[:len(first["records"])])
    need(errors, cursor_rows[0]["offset"] == len(prefix1) and
         cursor_rows[0]["prefix_sha256"] == sha256(prefix1) and
         cursor_rows[0]["next_sequence"] == len(first["records"]) + 1,
         "reader1:cursor-prefix")
    need(errors, cursor_rows[1]["offset"] == len(delivered_bytes) and
         cursor_rows[1]["prefix_sha256"] == sha256(delivered_bytes) and
         cursor_rows[1]["next_sequence"] == len(delivered) + 1,
         "reader2:cursor-prefix")
    need(errors, cursor_rows[2] == cursor_rows[1], "reader3:cursor-stable")

    commands = run_record.get("input_commands_sent")
    need(errors, commands == [{"op": "clock"}, {"op": "finish"}], "control:commands-only")
    command_events = [row for row in events if row.get("event") == "command"]
    need(errors, [row.get("command", {}).get("op") for row in command_events] == ["clock", "finish"],
         "control:producer-command-sequence")
    evaluation = next((row for row in delivered if row.get("event") == "independent_evaluation"), {})
    need(errors, evaluation.get("success") is False, "scope:no-task-success-claim")
    owner = json.loads((run / "producer" / "owner-events.json").read_text(encoding="utf-8"))
    need(errors, bool(owner), "input-owner:cleanup-record")
    for index, row in enumerate(owner):
        need(errors, row.get("verified") is True and row.get("keys_down") == [] and
             row.get("buttons_down") == [], f"input-owner:empty-release:{index}")
    for row in delivered:
        if row.get("event") == "observation":
            image_value = row.get("image")
            expected_prefix = run.as_posix().rstrip("/") + "/"
            need(errors, isinstance(image_value, str) and image_value.startswith(expected_prefix),
                 "observation:image-reference")
            if isinstance(image_value, str) and image_value.startswith(expected_prefix):
                image_file = run / image_value[len(expected_prefix):]
                need(errors, image_file.is_file(), "observation:image-present")

    disposition = "PASS_LIVE_PRODUCER_READ_SCOPED" if not errors else "FAIL_LIVE_READER_RECONCILIATION"
    return {
        "schema": "issue-3876-live-reader-audit-v1", "disposition": disposition,
        "allocation": freeze["allocation"], "producer_records": len(delivered),
        "reader_counts": [len(response.get("records", [])) for response in reader_responses],
        "live_reader_producer_alive": run_record.get("live_reader_producer_alive"),
        "authority_none_all_reads": all(r.get("authority") == "none" for r in reader_responses),
        "input_commands": commands, "errors": errors,
        "sha256": {"delivered.jsonl": sha256(delivered_bytes),
                   "events.jsonl": sha256(event_bytes),
                   "delivery-flush.jsonl": sha256(flush_bytes),
                   "producer_stdout.jsonl": sha256(stdout_bytes)},
        "freeze_input_count": len(actual_freeze_hashes),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--freeze", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = audit(args.repo.resolve(), args.run.resolve(), args.freeze.resolve())
    except Exception as exc:
        result = {"schema": "issue-3876-live-reader-audit-v1",
                  "disposition": "HOLD_EVIDENCE_INCOMPLETE",
                  "errors": [f"{type(exc).__name__}:{exc}"]}
    args.out.mkdir(parents=True, exist_ok=False)
    write_json = json.dumps(result, indent=2, sort_keys=True) + "\n"
    (args.out / "audit.json").write_text(write_json, encoding="utf-8")
    payload = (args.out / "audit.json").read_bytes()
    (args.out / "SHA256SUMS").write_text(f"{sha256(payload)}  audit.json\n", encoding="utf-8")
    print(write_json, end="")
    return 0 if result["disposition"] == "PASS_LIVE_PRODUCER_READ_SCOPED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
