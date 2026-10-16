"""Independently audit saved journal-mutex observations; execute no client or peer."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path, PurePosixPath


SOURCE_FILES = (
    "main_client.py", "send_proposal.py", "close_proposal.py",
    "composed_client.py", "bounded_journal_client.py", "echo_peer.py", "producer.py",
)
CELL_IDS = tuple(f"{v}__{c}" for v in ("main", "composed", "bounded_journal")
                 for c in ("healthy", "held_journal"))
VARIANT_SOURCES = {"main": "main_client.py", "composed": "composed_client.py",
                   "bounded_journal": "bounded_journal_client.py"}
CONSTANTS = {"request_timeout_ns": 50_000_000, "checkpoint_offset_ns": 250_000_000,
             "holder_release_offset_ns": 400_000_000, "cell_watchdog_ns": 6_000_000_000,
             "peer_readiness_timeout_ns": 2_000_000_000,
             "setup_rendezvous_timeout_ns": 1_000_000_000,
             "cleanup_join_timeout_ns": 350_000_000, "client_close_timeout_ns": 200_000_000}
REQUEST = {"method": "echo", "id": 1, "params": {"payload": "journal-mutex-witness"}}
RESULT = {"payload": "journal-mutex-witness"}
REQUEST_WIRE = (json.dumps(REQUEST, separators=(",", ":")) + "\n").encode("utf-8")
RESPONSE = {"id": 1, "result": RESULT}
RESPONSE_WIRE = (json.dumps(RESPONSE, separators=(",", ":")) + "\n").encode("utf-8")
ARTIFACT_FILES = {"events.jsonl", "peer_received.bin", "peer_responses.bin", "peer_events.jsonl",
                  "peer_ready.json", "journal.jsonl", "peer_stderr.bin",
                  "worker.stdout.bin", "worker.stderr.bin"}


class EvidenceError(ValueError):
    pass


def sha256(content):
    return hashlib.sha256(content).hexdigest()


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise EvidenceError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def decode_json(content):
    def nonfinite(value):
        raise EvidenceError(f"nonfinite JSON number: {value}")
    return json.loads(content.decode("utf-8"), object_pairs_hook=unique_object,
                      parse_constant=nonfinite)


def jsonl(content):
    if content and not content.endswith(b"\n"):
        raise EvidenceError("unterminated JSONL record")
    rows = []
    for line in content.splitlines():
        if not line:
            raise EvidenceError("empty JSONL record")
        row = decode_json(line)
        if not isinstance(row, dict):
            raise EvidenceError("JSONL record is not an object")
        rows.append(row)
    return rows


def timestamp(value, label):
    if type(value) is not int or value <= 0:
        raise EvidenceError(f"invalid timestamp: {label}")
    return value


def event_series(rows, label):
    times = []
    for index, row in enumerate(rows):
        if row.get("seq") != index or type(row.get("seq")) is not int:
            raise EvidenceError(f"nonconsecutive event sequence: {label}")
        if not isinstance(row.get("event"), str):
            raise EvidenceError(f"invalid event name: {label}")
        if set(row) != {"seq", "event", "monotonic_ns", "extra"} or not isinstance(row["extra"], dict):
            raise EvidenceError(f"invalid event fields: {label}")
        times.append(timestamp(row.get("monotonic_ns"), label))
    if times != sorted(times):
        raise EvidenceError(f"nonmonotonic event times: {label}")
    return rows


def one_event(events, name):
    found = [e for e in events if e["event"] == name]
    if len(found) != 1:
        raise EvidenceError(f"expected one event {name}, found {len(found)}")
    return found[0]


def artifact_entries(cell):
    inventory = cell.get("artifacts")
    if isinstance(inventory, dict):
        values = list(inventory.values())
    elif isinstance(inventory, list):
        values = inventory
    else:
        raise EvidenceError("artifact inventory must be a list or object")
    if any(not isinstance(entry, dict) for entry in values):
        raise EvidenceError("artifact inventory entry is not an object")
    return values


def artifacts_for(cell, root, overrides):
    content = {}
    cell_id = cell["cell_id"]
    for entry in artifact_entries(cell):
        if set(entry) != {"path", "bytes", "sha256"}:
            raise EvidenceError("malformed artifact inventory fields")
        relative = entry.get("path")
        if not isinstance(relative, str):
            raise EvidenceError("artifact path is not a string")
        path = PurePosixPath(relative)
        if path.is_absolute() or path.parts != (path.name,) or "\\" in relative:
            raise EvidenceError(f"artifact outside its cell: {relative}")
        if path.name not in ARTIFACT_FILES or path.name in content:
            raise EvidenceError(f"unexpected or duplicate artifact: {relative}")
        override_key = str(PurePosixPath("cells", cell_id, relative))
        resolved = (root / "cells" / cell_id / relative).resolve()
        if not resolved.is_relative_to(root.resolve()):
            raise EvidenceError(f"artifact escapes result root: {relative}")
        data = overrides[override_key] if override_key in overrides else resolved.read_bytes()
        if type(entry.get("bytes")) is not int or entry["bytes"] != len(data):
            raise EvidenceError(f"artifact byte count mismatch: {relative}")
        if entry.get("sha256") != sha256(data):
            raise EvidenceError(f"artifact hash mismatch: {relative}")
        content[path.name] = data
    if set(content) != ARTIFACT_FILES:
        raise EvidenceError("missing cell artifacts")
    return content


def fixture_contract(fixture, fixture_bytes, raw, source_dir):
    if not isinstance(fixture, dict) or not isinstance(raw, dict):
        raise EvidenceError("fixture/raw root is not an object")
    if fixture.get("schema") != "issue59-request-journal-composition-fixture-v1" or fixture.get("fixture_id") != "59-REQUEST-JOURNAL-MUTEX-COMPOSITION-4D74-A02":
        raise EvidenceError("fixture identity mismatch")
    if fixture.get("constants") != CONSTANTS or fixture.get("request") != REQUEST or fixture.get("expected_result") != RESULT or fixture.get("request_wire") != REQUEST_WIRE.decode("utf-8"):
        raise EvidenceError("fixture differs from independently pinned contract")
    expected_cells = [{"cell_id": identifier, "variant": identifier.split("__")[0],
                       "condition": identifier.split("__")[1],
                       "source_file": VARIANT_SOURCES[identifier.split("__")[0]]}
                      for identifier in CELL_IDS]
    if fixture.get("cells") != expected_cells:
        raise EvidenceError("fixture cell keys/order mismatch")
    scope = fixture.get("scope", {})
    if scope.get("os_send_entry_measured") is not False or scope.get("file_write_flush_bound") is not False or scope.get("whole_call_hard_bound") is not False or scope.get("mutex_acquisition_only") is not True:
        raise EvidenceError("fixture scope exceeds measured boundary")
    if raw.get("schema") != "issue59-request-journal-composition-v1" or raw.get("fixture_id") != fixture["fixture_id"] or raw.get("fixture_sha256") != sha256(fixture_bytes):
        raise EvidenceError("raw fixture/schema custody mismatch")
    actual = {name: sha256((source_dir / name).read_bytes()) for name in SOURCE_FILES}
    if fixture.get("source_sha256") != actual or raw.get("source_custody") != actual or raw.get("sources_after") != actual:
        raise EvidenceError("source before/after/freeze hash mismatch")
    if raw.get("status") != "COMPLETE" or raw.get("preflight_errors") != [] or raw.get("scope") != fixture["scope"]:
        raise EvidenceError("producer preflight/status/scope STOP")
    producer = raw.get("producer")
    if not isinstance(producer, dict) or type(producer.get("pid")) is not int or producer["pid"] <= 0 or not isinstance(producer.get("platform"), str) or not producer["platform"].startswith("Linux-"):
        raise EvidenceError("producer is not identified as actual Linux")
    if not isinstance(producer.get("executable"), str) or not producer["executable"].startswith("/") or not isinstance(producer.get("python"), str):
        raise EvidenceError("missing producer Python provenance")
    began = timestamp(producer.get("started_monotonic_ns"), "producer_start")
    ended = timestamp(producer.get("finished_monotonic_ns"), "producer_finish")
    if began >= ended:
        raise EvidenceError("producer temporal order")
    clocks = producer.get("clock_info", {})
    records = [clocks.get("monotonic"), clocks.get("perf_counter")]
    for record in records:
        if not isinstance(record, dict) or record.get("monotonic") is not True or record.get("adjustable") is not False or type(record.get("resolution")) not in (int, float) or not math.isfinite(record["resolution"]) or record["resolution"] <= 0:
            raise EvidenceError("invalid saved clock qualification")
    if not records[0].get("implementation") or records[0]["implementation"] != records[1].get("implementation"):
        raise EvidenceError("driver/journal clocks not independently qualified as same implementation")
    return actual, producer


def peer_evidence(files, start, cell):
    ready = decode_json(files["peer_ready.json"])
    if not isinstance(ready, dict) or type(ready.get("pid")) is not int or ready["pid"] <= 0:
        raise EvidenceError("invalid peer ready PID")
    ready_at = timestamp(ready.get("monotonic_ns"), "peer_ready")
    if ready_at > start:
        raise EvidenceError("peer not ready before caller")
    if cell["final"].get("child_pid") != ready["pid"] or ready.get("parent_pid") != cell.get("worker_pid"):
        raise EvidenceError("peer ready/final PID mismatch")
    events = event_series(jsonl(files["peer_events.jsonl"]), "peer")
    if not events or events[0]["event"] != "peer_ready" or any(sum(e["event"] == name for e in events) > 1 for name in ("stdin_eof", "peer_exit")):
        raise EvidenceError("malformed/duplicate peer lifecycle events")
    ready_event = one_event(events, "peer_ready")
    if ready_event["monotonic_ns"] != ready_at or ready_event["extra"] != {"pid": ready["pid"], "parent_pid": ready.get("parent_pid")}:
        raise EvidenceError("peer ready file/event mismatch")
    chunks, requests, responses = [], [], []
    pending = b""
    for event in events:
        extra = event["extra"]
        if event["event"] == "read_chunk":
            chunk = bytes.fromhex(extra["bytes_hex"])
            if not chunk or extra.get("bytes") != len(chunk) or event["monotonic_ns"] < start:
                raise EvidenceError("invalid/pre-request peer chunk")
            chunks.append(chunk)
            pending += chunk
        elif event["event"] == "complete_jsonl":
            wire = bytes.fromhex(extra["raw_hex"])
            if wire != REQUEST_WIRE or extra.get("parsed") != REQUEST or extra.get("bytes") != len(wire):
                raise EvidenceError("peer request differs from exact echo request")
            if not pending.startswith(wire):
                raise EvidenceError("peer JSONL completion precedes/mismatches received chunks")
            pending = pending[len(wire):]
            requests.append(event)
        elif event["event"] == "response_written":
            wire = bytes.fromhex(extra["raw_hex"])
            if wire != RESPONSE_WIRE or extra.get("bytes") != len(wire) or extra.get("parsed") != RESPONSE:
                raise EvidenceError("peer response differs from exact echo response")
            if len(requests) != len(responses) + 1:
                raise EvidenceError("peer response has no preceding completed request")
            responses.append(event)
        elif event["event"] == "stdin_eof":
            if extra.get("pending_hex") != pending.hex():
                raise EvidenceError("peer EOF pending-byte reconstruction mismatch")
        elif event["event"] not in ("peer_ready", "stdin_eof", "peer_exit"):
            raise EvidenceError("unexpected/error peer event")
    if b"".join(chunks) != files["peer_received.bin"]:
        raise EvidenceError("peer chunk/wire reconstruction mismatch")
    if len(requests) != len(responses) or len(requests) > 1:
        raise EvidenceError("peer request/response count mismatch")
    if files["peer_responses.bin"] != b"".join(bytes.fromhex(e["extra"]["raw_hex"]) for e in responses):
        raise EvidenceError("peer response event/bytes reconstruction mismatch")
    if requests and not requests[0]["monotonic_ns"] <= responses[0]["monotonic_ns"]:
        raise EvidenceError("peer response predates request")
    if cell["final"]["child_returncode"] == 0:
        if one_event(events, "stdin_eof")["extra"] != {"pending_hex": ""} or one_event(events, "peer_exit")["extra"] != {"exit_code": 0}:
            raise EvidenceError("normal peer exit/EOF evidence missing")
    return events, requests, responses


def check_cleanup(cell, events, finished):
    final = cell.get("final")
    if not isinstance(final, dict):
        raise EvidenceError("missing final cleanup")
    if set(final) != {"caller_alive", "reader_alive", "holder_alive", "child_pid", "child_returncode", "explicit_pipe_closed", "journal_closed", "peer_received_bytes", "journal_row_count", "cleanup_errors", "thread_exceptions"} or type(final.get("child_pid")) is not int or final["child_pid"] <= 0 or type(final.get("peer_received_bytes")) is not int or type(final.get("journal_row_count")) is not int:
        raise EvidenceError("malformed final cleanup fields")
    if any(final.get(key) is not False for key in ("caller_alive", "reader_alive", "holder_alive")):
        raise EvidenceError("thread alive at cleanup endpoint")
    if type(final.get("child_returncode")) is not int:
        raise EvidenceError("child not reaped at cleanup endpoint")
    if final.get("explicit_pipe_closed") != {"stdin": True, "stdout": True, "stderr": True} or final.get("journal_closed") is not True or final.get("cleanup_errors") != [] or final.get("thread_exceptions") != []:
        raise EvidenceError("incomplete/error cleanup endpoint")
    if any(type(value) is not bool for value in final["explicit_pipe_closed"].values()):
        raise EvidenceError("malformed pipe cleanup booleans")
    cleanup = one_event(events, "cleanup_done")
    if cleanup.get("extra") != final or cleanup["monotonic_ns"] < finished:
        raise EvidenceError("cleanup endpoint event mismatch/order")
    reaped = one_event(events, "child_reaped")
    if reaped["extra"] != {"child_pid": final["child_pid"], "returncode": final["child_returncode"]}:
        raise EvidenceError("saved child reap endpoint mismatch")
    for name in ("caller_joined", "reader_joined"):
        if one_event(events, name)["extra"] != {"alive": False}:
            raise EvidenceError("saved thread join endpoint mismatch")
    for name in ("stdin", "stdout", "stderr"):
        closed = [e for e in events if e["event"] == "pipe_closed" and e["extra"].get("name") == name]
        if len(closed) != 1 or any(e["extra"] != {"name": name, "closed": True} for e in closed):
            raise EvidenceError("saved explicit pipe endpoint mismatch")
    eof_close = one_event(events, "stdin_closed_for_peer_eof")
    if eof_close["extra"] != {"closed": True} or not finished <= eof_close["monotonic_ns"] <= reaped["monotonic_ns"]:
        raise EvidenceError("stdin close-before-reap evidence mismatch")
    if one_event(events, "journal_closed")["extra"] != {"closed": True}:
        raise EvidenceError("saved journal close endpoint mismatch")
    close_begin, close_end = one_event(events, "client_close_begin"), one_event(events, "client_close_returned")
    if close_begin["extra"] != {"timeout_ns": CONSTANTS["client_close_timeout_ns"]} or not finished <= reaped["monotonic_ns"] <= close_begin["monotonic_ns"] <= close_end["monotonic_ns"] <= cleanup["monotonic_ns"]:
        raise EvidenceError("saved cleanup order/configuration mismatch")


def check_cell(cell, files, source_hashes, producer):
    if cell.get("status") != "COMPLETE":
        raise EvidenceError("cell engine STOP/incomplete")
    cell_id = cell["cell_id"]
    variant, condition = cell_id.split("__")
    if cell.get("variant") != variant or cell.get("condition") != condition or cell.get("source_file") != VARIANT_SOURCES[variant]:
        raise EvidenceError("cell variant/condition mismatch")
    if cell.get("source_custody") != source_hashes or cell.get("sources_after") != source_hashes or cell.get("stop_reason") is not None:
        raise EvidenceError("cell source/status custody mismatch")
    supervisor = cell.get("supervisor", {})
    if supervisor.get("started") is not True or supervisor.get("watchdog_fired") is not False or supervisor.get("worker_returncode") != 0 or type(supervisor.get("worker_returncode")) is not int or supervisor.get("kill_error") is not None or supervisor.get("supervision_error") is not None or supervisor.get("capture_error") is not None or supervisor.get("containment_failed") is not False or supervisor.get("worker_pipe_closed") != {"stdout": True, "stderr": True}:
        raise EvidenceError("cell supervisor/watchdog STOP")
    if type(cell.get("worker_pid")) is not int or cell["worker_pid"] <= 0 or supervisor.get("worker_pid") != cell["worker_pid"] or cell.get("worker_parent_pid") != producer["pid"]:
        raise EvidenceError("worker supervisor/parent PID mismatch")
    worker_start = timestamp(supervisor.get("started_monotonic_ns"), "worker_start")
    worker_finish = timestamp(supervisor.get("finished_monotonic_ns"), "worker_finish")
    if not producer["started_monotonic_ns"] <= worker_start < worker_finish <= producer["finished_monotonic_ns"] or worker_finish - worker_start > CONSTANTS["cell_watchdog_ns"]:
        raise EvidenceError("worker exceeded watchdog/provenance interval")
    command = supervisor.get("command")
    if not isinstance(command, list) or len(command) != 9 or command[0] != producer["executable"] or command[1] != "-B" or PurePosixPath(command[2]).name != "producer.py" or command[3] != "--fixture" or PurePosixPath(command[4]).name != "fixture.json" or command[5:8] != ["--cell", cell_id, "--cell-dir"] or PurePosixPath(command[8]).parts[-2:] != ("cells", cell_id):
        raise EvidenceError("worker command differs from saved real-cell entry point")
    peer_command = cell.get("peer_command")
    if not isinstance(peer_command, list) or len(peer_command) != 5 or peer_command[0] != producer["executable"] or peer_command[1] != "-B" or PurePosixPath(peer_command[2]).name != "echo_peer.py" or peer_command[3] != "--directory" or peer_command[4] != command[8]:
        raise EvidenceError("peer command differs from real echo-child entry point")
    events = event_series(jsonl(files["events.jsonl"]), "cell")
    allowed_events = {"cell_started", "client_construct_begin", "client_constructed", "peer_ready_observed", "caller_started", "caller_finished", "checkpoint", "holder_acquired", "holder_wait", "holder_release_begin", "holder_released", "holder_joined", "caller_joined", "pipe_close_begin", "stdin_closed_for_peer_eof", "pipe_closed", "child_terminate", "child_kill", "child_reaped", "client_close_begin", "client_close_returned", "reader_joined", "driver_journal_close_begin", "journal_closed", "cleanup_done", "cell_finished"}
    if any(e["event"] not in allowed_events for e in events) or not events or events[0]["event"] != "cell_started" or events[-1]["event"] != "cell_finished" or not worker_start <= events[0]["monotonic_ns"] <= events[-1]["monotonic_ns"] <= worker_finish:
        raise EvidenceError("cell event boundary/order/error mismatch")
    if one_event(events, "cell_finished")["extra"] != {"status": "COMPLETE", "stop_reason": None}:
        raise EvidenceError("cell finish event STOP")
    spec = {"cell_id": cell_id, "variant": variant, "condition": condition,
            "source_file": VARIANT_SOURCES[variant]}
    if one_event(events, "cell_started")["extra"] != {"spec": spec} or one_event(events, "client_construct_begin")["extra"] != {"peer_command": peer_command}:
        raise EvidenceError("cell/source/Popen command event mismatch")
    constructed = one_event(events, "client_constructed")
    if constructed["extra"].get("child_pid") != cell["final"].get("child_pid") or not isinstance(constructed["extra"].get("reader_name"), str):
        raise EvidenceError("constructed child/reader identity mismatch")
    times = cell.get("timestamps", {})
    if not isinstance(times, dict) or set(times) != {"caller_started_ns", "checkpoint_ns", "caller_finished_ns", "holder_acquired_ns", "holder_release_begin_ns", "holder_released_ns"}:
        raise EvidenceError("malformed timestamp fields")
    start = timestamp(times.get("caller_started_ns"), "caller_start")
    checkpoint = timestamp(times.get("checkpoint_ns"), "checkpoint")
    finish = timestamp(times.get("caller_finished_ns"), "caller_finish")
    if not start <= checkpoint or not start <= finish:
        raise EvidenceError("caller/checkpoint temporal order")
    if checkpoint - start < CONSTANTS["checkpoint_offset_ns"]:
        raise EvidenceError("checkpoint before frozen observation offset")
    if max(checkpoint, finish) - start >= CONSTANTS["cell_watchdog_ns"]:
        raise EvidenceError("cell exceeded frozen watchdog")
    for event_name, value in (("caller_started", start), ("checkpoint", checkpoint), ("caller_finished", finish)):
        event = one_event(events, event_name)
        if event["monotonic_ns"] != value:
            raise EvidenceError(f"row/event timestamp mismatch: {event_name}")
    if one_event(events, "caller_started")["extra"] != {"timeout_ns": CONSTANTS["request_timeout_ns"]}:
        raise EvidenceError("request timeout differs from frozen budget")
    ready = decode_json(files["peer_ready.json"])
    ready_observed = one_event(events, "peer_ready_observed")
    if ready_observed["extra"] != {"ready": ready} or not one_event(events, "client_construct_begin")["monotonic_ns"] <= ready["monotonic_ns"] <= ready_observed["monotonic_ns"] <= start:
        raise EvidenceError("peer readiness event/temporal custody mismatch")
    snapshot = cell.get("checkpoint")
    if not isinstance(snapshot, dict) or one_event(events, "checkpoint").get("extra") != snapshot:
        raise EvidenceError("checkpoint row/event mismatch")
    if set(snapshot) != {"caller_alive", "caller_finished", "reader_alive", "peer_returncode", "peer_received_bytes", "journal_row_count", "holder_alive", "holder_finished"} or any(type(snapshot[key]) is not bool for key in ("caller_alive", "caller_finished", "reader_alive", "holder_alive", "holder_finished")):
        raise EvidenceError("malformed checkpoint fields")
    if type(snapshot.get("peer_received_bytes")) is not int or type(snapshot.get("journal_row_count")) is not int or snapshot["peer_received_bytes"] < 0 or snapshot["journal_row_count"] < 0:
        raise EvidenceError("invalid checkpoint counts")
    if snapshot.get("reader_alive") is not True or snapshot.get("peer_returncode") is not None:
        raise EvidenceError("reader/peer unhealthy at checkpoint")
    caller = cell.get("caller")
    if not isinstance(caller, dict) or one_event(events, "caller_finished").get("extra") != caller:
        raise EvidenceError("caller row/event mismatch")
    if not ((caller.get("status") == "RETURN" and set(caller) == {"status", "result"}) or (caller.get("status") == "EXCEPTION" and set(caller) == {"status", "exception_type", "message"} and isinstance(caller["exception_type"], str) and isinstance(caller["message"], str))):
        raise EvidenceError("malformed or unfinished caller outcome")
    if snapshot.get("caller_alive") is not (finish > checkpoint):
        raise EvidenceError("caller checkpoint state contradicts timestamps")
    if snapshot.get("caller_finished") is not (finish < checkpoint):
        raise EvidenceError("caller completion marker contradicts timestamps")
    check_cleanup(cell, events, finish)
    if files["peer_stderr.bin"] or files["worker.stderr.bin"] or files["worker.stdout.bin"]:
        raise EvidenceError("peer/worker emitted unexpected stderr/stdout")
    peer_events, requests, responses = peer_evidence(files, start, cell)
    if any(e["monotonic_ns"] > one_event(events, "cleanup_done")["monotonic_ns"] for e in peer_events):
        raise EvidenceError("peer event after final cleanup endpoint")
    journal = jsonl(files["journal.jsonl"])
    if cell["final"].get("peer_received_bytes") != len(files["peer_received.bin"]) or cell["final"].get("journal_row_count") != len(journal):
        raise EvidenceError("final byte/journal count contradicts saved artifacts")
    for row in journal:
        if set(row) != {"direction", "observed_ns", "message"} or row["direction"] not in ("sent", "received"):
            raise EvidenceError("malformed journal row")
        if not start <= timestamp(row["observed_ns"], "journal") <= finish:
            raise EvidenceError("journal observation outside caller interval")
    if [r["observed_ns"] for r in journal] != sorted(r["observed_ns"] for r in journal):
        raise EvidenceError("nonmonotonic journal timestamps")
    held = condition == "held_journal"
    if held:
        acquired = timestamp(times.get("holder_acquired_ns"), "holder_acquired")
        release_begin = timestamp(times.get("holder_release_begin_ns"), "holder_release_begin")
        released = timestamp(times.get("holder_released_ns"), "holder_released")
        if not acquired < start <= checkpoint < release_begin <= released or release_begin - start < CONSTANTS["holder_release_offset_ns"]:
            raise EvidenceError("holder ordering/release offset invalid")
        for name, value in (("holder_acquired", acquired), ("holder_release_begin", release_begin), ("holder_released", released)):
            if one_event(events, name)["monotonic_ns"] != value:
                raise EvidenceError("holder row/event mismatch")
        if one_event(events, "holder_wait")["extra"] != {"release_target_ns": start + CONSTANTS["holder_release_offset_ns"]} or one_event(events, "holder_joined")["extra"] != {"alive": False}:
            raise EvidenceError("holder target/join evidence mismatch")
        if snapshot.get("holder_alive") is not True or snapshot.get("holder_finished") is not False:
            raise EvidenceError("holder not held/live at checkpoint")
        if snapshot["peer_received_bytes"] != 0 or snapshot["journal_row_count"] != 0:
            raise EvidenceError("held checkpoint already has peer/journal bytes")
    elif any(times.get(key) is not None for key in ("holder_acquired_ns", "holder_release_begin_ns", "holder_released_ns")) or any(e["event"].startswith("holder_") for e in events) or snapshot.get("holder_alive") is not False or snapshot.get("holder_finished") is not False:
        raise EvidenceError("healthy cell claims a holder")
    method_errors = []
    expects_echo = not held or variant == "main"
    if expects_echo:
        if caller.get("status") != "RETURN" or caller.get("result") != RESULT:
            method_errors.append("exact_echo_outcome_missing")
        if files["peer_received.bin"] != REQUEST_WIRE or len(requests) != 1 or len(responses) != 1:
            method_errors.append("exact_peer_echo_missing")
        journal_matches = len(journal) == 2
        if journal_matches:
            journal_matches = journal == [
                {"direction": "sent", "observed_ns": journal[0]["observed_ns"], "message": REQUEST},
                {"direction": "received", "observed_ns": journal[1]["observed_ns"], "message": RESPONSE},
            ]
        if not journal_matches:
            method_errors.append("exact_sent_received_journal_missing")
        if not held and (snapshot["peer_received_bytes"] != len(REQUEST_WIRE) or snapshot["journal_row_count"] != 2):
            method_errors.append("healthy_checkpoint_echo_evidence_missing")
        if held:
            if finish < released or snapshot.get("caller_alive") is not True or requests and requests[0]["monotonic_ns"] < release_begin:
                method_errors.append("main_held_did_not_finish_after_release")
        elif finish - start > CONSTANTS["checkpoint_offset_ns"]:
            method_errors.append("healthy_echo_exceeded_observation_bound")
    else:
        if caller.get("status") != "EXCEPTION" or caller.get("exception_type") != "TimeoutError":
            method_errors.append("expected_timeout_missing")
        if files["peer_received.bin"] or requests or responses:
            method_errors.append("timeout_cell_has_peer_bytes")
        if variant == "composed":
            if caller.get("message") != "app-server send budget expired; no send attempted":
                method_errors.append("composed_timeout_branch_message_mismatch")
            if finish < released or snapshot.get("caller_alive") is not True:
                method_errors.append("composed_timeout_not_after_release")
            if len(journal) != 1 or journal[0].get("direction") != "sent" or journal[0].get("message") != REQUEST:
                method_errors.append("composed_sent_journal_missing")
        else:
            if caller.get("message") != "app-server sent journal lock timed out; no send attempted":
                method_errors.append("bounded_timeout_branch_message_mismatch")
            if finish >= checkpoint or snapshot.get("caller_alive") is not False:
                method_errors.append("bounded_timeout_not_before_checkpoint")
            if journal:
                method_errors.append("bounded_timeout_has_journal_row")
    return {"cell_id": cell_id, "elapsed_ns": finish - start,
            "peer_received_bytes": len(files["peer_received.bin"]), "journal_rows": len(journal),
            "method_errors": method_errors}


def audit_once(fixture, fixture_bytes, raw, source_dir, artifact_dir, overrides=None):
    result = {"schema": "issue59-request-journal-independent-audit-v1", "result": "STOP",
              "engine_errors": [], "method_errors": [], "cells": []}
    overrides = {} if overrides is None else overrides
    try:
        source_hashes, producer = fixture_contract(fixture, fixture_bytes, raw, Path(source_dir))
        cells = raw.get("cells")
        if not isinstance(cells, list) or any(not isinstance(c, dict) for c in cells):
            raise EvidenceError("invalid cells collection")
        ids = [c.get("cell_id") for c in cells]
        if len(ids) != 6 or len(set(ids)) != 6 or tuple(ids) != CELL_IDS:
            raise EvidenceError("missing/duplicate/unexpected cell keys")
        previous_finish = producer["started_monotonic_ns"]
        for cell in cells:
            try:
                worker_start = timestamp(cell.get("supervisor", {}).get("started_monotonic_ns"), "sequential_worker_start")
                worker_finish = timestamp(cell.get("supervisor", {}).get("finished_monotonic_ns"), "sequential_worker_finish")
                if worker_start < previous_finish:
                    raise EvidenceError("formal cells overlapped or were reordered")
                previous_finish = worker_finish
                files = artifacts_for(cell, Path(artifact_dir), overrides)
                checked = check_cell(cell, files, source_hashes, producer)
                result["cells"].append(checked)
                result["method_errors"].extend(f"{cell['cell_id']}:{e}" for e in checked["method_errors"])
            except (OSError, ValueError, TypeError, KeyError, IndexError, AttributeError) as exc:
                result["engine_errors"].append(f"{cell.get('cell_id')}:{type(exc).__name__}:{exc}")
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        result["engine_errors"].append(f"{type(exc).__name__}:{exc}")
    if not result["engine_errors"]:
        result["result"] = "FAIL_METHOD" if result["method_errors"] else "PASS_SCOPED_COUNTEREXAMPLE"
    result["scope"] = "Six saved Linux Popen echo-child cells only; empty peer bytes establish no child receipt. No OS-send syscall counter was collected; no-send is source-derived. Journal observed_ns is recorded before mutex acquisition and does not timestamp file-write completion."
    return result


def replace_saved_jsonl(cell, filename, transform, root, overrides):
    entries = artifact_entries(cell)
    entry = next(e for e in entries if PurePosixPath(e["path"]).name == filename)
    relative = str(PurePosixPath("cells", cell["cell_id"], entry["path"]))
    rows = jsonl((Path(root) / relative).read_bytes())
    transform(rows)
    data = b"".join((json.dumps(r, separators=(",", ":")) + "\n").encode("utf-8") for r in rows)
    overrides[relative] = data
    entry["bytes"], entry["sha256"] = len(data), sha256(data)


def mutation_controls(fixture, fixture_bytes, raw, source_dir, artifact_dir):
    controls = {}
    for name in ("timestamp", "peer_byte", "outcome", "duplicate", "cleanup"):
        mutant, overrides = copy.deepcopy(raw), {}
        try:
            by_id = {c["cell_id"]: c for c in mutant["cells"]}
            if name == "timestamp":
                cell = by_id["main__held_journal"]
                forged = cell["timestamps"]["caller_started_ns"] + 300_000_000
                cell["timestamps"]["holder_release_begin_ns"] = forged
                def change(rows):
                    one_event(rows, "holder_release_begin")["monotonic_ns"] = forged
                replace_saved_jsonl(cell, "events.jsonl", change, artifact_dir, overrides)
            elif name == "peer_byte":
                cell = by_id["main__healthy"]
                entry = next(e for e in artifact_entries(cell) if PurePosixPath(e["path"]).name == "peer_received.bin")
                relative = str(PurePosixPath("cells", cell["cell_id"], entry["path"]))
                data = b"[" + (Path(artifact_dir) / relative).read_bytes()[1:]
                overrides[relative] = data
                entry["bytes"], entry["sha256"] = len(data), sha256(data)
            elif name == "outcome":
                cell = by_id["main__healthy"]
                cell["caller"]["result"] = {"payload": "forged"}
                def change(rows):
                    one_event(rows, "caller_finished")["extra"] = copy.deepcopy(cell["caller"])
                replace_saved_jsonl(cell, "events.jsonl", change, artifact_dir, overrides)
            elif name == "duplicate":
                mutant["cells"].append(copy.deepcopy(mutant["cells"][0]))
            else:
                cell = by_id["composed__healthy"]
                cell["final"]["reader_alive"] = True
                def change(rows):
                    one_event(rows, "cleanup_done")["extra"] = copy.deepcopy(cell["final"])
                replace_saved_jsonl(cell, "events.jsonl", change, artifact_dir, overrides)
            checked = audit_once(fixture, fixture_bytes, mutant, source_dir, artifact_dir, overrides)
            controls[name] = {"rejected": checked["result"] != "PASS_SCOPED_COUNTEREXAMPLE",
                              "result": checked["result"], "engine_errors": checked["engine_errors"],
                              "method_errors": checked["method_errors"]}
        except (OSError, ValueError, TypeError, KeyError, StopIteration, AttributeError) as exc:
            controls[name] = {"rejected": False, "result": "CONTROL_CONSTRUCTION_ERROR",
                              "error": f"{type(exc).__name__}:{exc}"}
    return controls


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--raw", required=True)
    parser.add_argument("--source-dir", default=str(Path(__file__).parent))
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    try:
        fixture_bytes = Path(args.fixture).read_bytes()
        fixture, raw = decode_json(fixture_bytes), decode_json(Path(args.raw).read_bytes())
        result = audit_once(fixture, fixture_bytes, raw, args.source_dir, Path(args.raw).parent)
        if result["result"] == "PASS_SCOPED_COUNTEREXAMPLE":
            controls = mutation_controls(fixture, fixture_bytes, raw, args.source_dir, Path(args.raw).parent)
            result["corruption_controls"] = controls
            result["corruptions_rejected"] = sum(c["rejected"] for c in controls.values())
            if result["corruptions_rejected"] != 5:
                result["result"] = "STOP"
                result["engine_errors"].append("audit mutation control failed")
        else:
            result["corruption_controls"] = {}
            result["corruptions_rejected"] = 0
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        result = {"schema": "issue59-request-journal-independent-audit-v1", "result": "STOP",
                  "engine_errors": [f"{type(exc).__name__}:{exc}"], "method_errors": [],
                  "cells": [], "corruption_controls": {}, "corruptions_rejected": 0}
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n")
    print(result["result"])
    print(f"cells_checked={len(result['cells'])}; corruptions_rejected={result['corruptions_rejected']}/5")
    raise SystemExit(0 if result["result"] == "PASS_SCOPED_COUNTEREXAMPLE" else 1)


if __name__ == "__main__":
    main()
