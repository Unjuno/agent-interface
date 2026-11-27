"""Read-only, pre-admission viewport witness for a single proposed cover renewal."""
from copy import deepcopy
from pathlib import Path
import re
import secrets
import threading
import time

from PIL import Image

from doom_signal_value_domain_v1 import signal_value_in_domain
from executor_v11 import program_sha256
from doom_typed_observation_v1 import _same_exact_json_value, extract_typed_observation, frame_rgb_sha256


EVENT = "cover_renewal_passive_observation"
IDENTIFIER = re.compile(r"cover-[0-9]+-renew-[0-9]+")
DIGEST = re.compile(r"[0-9a-f]{64}")
PROBE_NS = 1_000_000_000


def probe_frame_path(output, identifier):
    if type(identifier) is not str or not IDENTIFIER.fullmatch(identifier):
        raise ValueError("exact renewal identifier required")
    return Path(output) / f"{identifier}-passive.png"


def verify_probe_frame(output, witness, readers):
    with Image.open(probe_frame_path(output, witness["id"])) as frame:
        if frame_rgb_sha256(frame) != witness["frame_rgb_sha256"]:
            raise ValueError("passive renewal frame digest mismatch")
        metadata = {"sequence": witness["source_sequence"], "capture_ns": witness["capture_ns"],
                    "pointer_binding": witness["pointer_binding"]}
        fields = ("status", "signal_id", "value", "sequence", "capture_ns", "binding", "wad_sha256")
        for key in ("health", "ammo"):
            measured = readers[key].read_frame(metadata, frame)
            reported = witness["signals"][key]
            if not all(field in measured and field in reported and
                       _same_exact_json_value(measured[field], reported[field]) for field in fields):
                raise ValueError("passive renewal HUD differs from the retained frame")


def capture_passive_probe(identifier, previous, source, *,
                          read_proof, grab_frame, readers, publish_frame, deadline,
                          clock=time.perf_counter_ns):
    """Capture a current screen through an independent, read-only connection."""
    if type(identifier) is not str or not IDENTIFIER.fullmatch(identifier):
        raise ValueError("exact renewal identifier required")
    started = clock()
    if (type(deadline) is not int or not 0 < deadline - started <= PROBE_NS
            or type(previous.get("intent_token")) is not str or not previous["intent_token"]):
        raise ValueError("exact renewal deadline and prior intent required")
    sequence = source["sequence"]
    expected = {"pointer_binding": source["pointer_binding"],
                "process_digest": source["target_process_identity"]["digest"],
                "window_digest": source["target_renewal_window_identity"]["digest"]}
    before = read_proof(deadline)
    if not _same_exact_json_value(before, expected) or clock() >= deadline:
        raise ValueError("passive renewal target unverified before capture")
    frame = grab_frame()
    captured = clock()
    after = read_proof(deadline)
    if not _same_exact_json_value(after, before) or captured >= deadline or clock() >= deadline:
        raise ValueError("passive renewal target changed or capture expired")
    typed = extract_typed_observation(
        frame, {"id": identifier, "step": 0, "sequence": sequence, "capture_ns": captured,
                "pointer_binding": expected["pointer_binding"]}, readers, clock=clock)
    publish_frame(frame)
    completed = clock()
    if not started <= captured <= completed < deadline:
        raise ValueError("passive renewal completed too late")
    return {
        "event": EVENT, "id": identifier, "previous_cover_id": previous["id"],
        "previous_intent_token": previous["intent_token"], "deadline_ns": deadline,
        "previous_program_sha256": source["previous_program_sha256"], "probe_sequence": int(identifier.rsplit("-", 1)[1]),
        "source_sequence": sequence, "input_owner_generation": source["input_owner_generation"],
        "renewal_owner_id": source["renewal_owner_id"],
        "pointer_binding": deepcopy(expected["pointer_binding"]),
        "target_process_identity": deepcopy(source["target_process_identity"]),
        "target_renewal_window_identity": deepcopy(source["target_renewal_window_identity"]),
        "capture_started_ns": started, "capture_ns": captured, "capture_completed_ns": completed,
        "frame_rgb_sha256": typed["frame_rgb_sha256"], "signals": typed["signals"],
        "grants_input_authority": False,
    }


def evaluate_passive_probe(row, identifier, previous, source, guards, *, started_ns, observed_ns):
    """Evaluate existing policy without advancing the Executor's observation sequence."""
    custody_fields = ("input_owner_generation", "pointer_binding",
                      "target_process_identity", "target_renewal_window_identity", "renewal_owner_id")
    if (type(row) is not dict or row.get("event") != EVENT or row.get("id") != identifier
            or row.get("previous_cover_id") != previous["id"]
            or type(previous.get("intent_token")) is not str or not previous["intent_token"]
            or row.get("previous_intent_token") != previous["intent_token"]
            or type(row.get("previous_program_sha256")) is not str
            or not DIGEST.fullmatch(row["previous_program_sha256"])
            or row["previous_program_sha256"] != previous.get("program_sha256")
            or type(row.get("probe_sequence")) is not int
            or row["probe_sequence"] != int(identifier.rsplit("-", 1)[1])
            or type(row.get("approval_nonce")) is not str
            or len(row["approval_nonce"]) != 32
            or any(char not in "0123456789abcdef" for char in row["approval_nonce"])
            or type(row.get("deadline_ns")) is not int or row["deadline_ns"] != started_ns + PROBE_NS
            or type(row.get("source_sequence")) is not int or row["source_sequence"] != source["sequence"]
            or row.get("grants_input_authority") is not False
            or any(key not in row or key not in source
                   or not _same_exact_json_value(row[key], source[key]) for key in custody_fields)
            or type(row.get("frame_rgb_sha256")) is not str or not DIGEST.fullmatch(row["frame_rgb_sha256"])
            or any(type(row.get(name)) is not int
                   for name in ("capture_started_ns", "capture_ns", "capture_completed_ns"))
            or not previous["terminal_ns"] <= started_ns <= row["capture_started_ns"] <= row["capture_ns"]
                <= row["capture_completed_ns"] <= observed_ns
            or observed_ns - started_ns > PROBE_NS
            or row["capture_ns"] <= source["capture_ns"]):
        raise ValueError("passive renewal proof stale or custody unverified")
    signals = row.get("signals")
    if (type(signals) is not dict or set(signals) != {"health", "ammo"}
            or any(type(signal) is not dict or signal.get("signal_id") != name
                   or signal.get("format") != "observable-signal-v1" or signal.get("status") != "observed"
                   or not signal_value_in_domain(name, signal.get("value"))
                   or type(signal.get("sequence")) is not int or signal["sequence"] != row["source_sequence"]
                   or type(signal.get("capture_ns")) is not int or signal["capture_ns"] != row["capture_ns"]
                   or signal.get("binding") != row["pointer_binding"]
                   for name, signal in signals.items())):
        raise ValueError("passive renewal HUD data unverified")
    for name, guard in guards.items():
        outcome = guard.evaluate_passive(signals[name])
        if outcome["requires_new_decision"]:
            return {"event": "policy_invalidation", "reason": f"{name}:{outcome['reason']}",
                    "probe_id": identifier, "capture_ns": row["capture_ns"], "outcome": outcome,
                    "requires_new_decision": True, "grants_input_authority": False}
    return None


def request_passive_probe(send, receive, identifier, previous, source, guards, *, done,
                          verify_frame, clock=time.perf_counter_ns):
    started = clock()
    deadline = started + PROBE_NS
    send({"op": "probe_cover_renewal", "id": identifier, "previous_cover_id": previous["id"],
          "previous_intent_token": previous["intent_token"], "expected_sequence": source["sequence"],
          "deadline_ns": deadline})
    row = receive(identifier, deadline)
    if type(row) is dict and row.get("event") == EVENT:
        verify_frame(row)
    invalidation = evaluate_passive_probe(row, identifier, previous, source, guards,
                                          started_ns=started, observed_ns=clock())
    planner_completed = done()
    return {"admit_renewal": not planner_completed and invalidation is None,
            "planner_completed": planner_completed, "invalidation": invalidation,
            "witness": row}


def settled_cover_probe_source(executor, backend, terminal, accepted, command):
    if not executor.lock.acquire(blocking=False):
        raise ValueError("executor unavailable for passive renewal")
    try:
        expected = command["previous_cover_id"]
        if (executor.closed or executor.active is not None or type(terminal) is not dict
                or terminal.get("id") != expected or terminal.get("status") not in ("completed", "expired")
                or type(accepted) is not dict or accepted.get("id") != expected
                or accepted.get("intent_token") != command["previous_intent_token"]):
            raise ValueError("previous cover terminal is not settled")
        release = terminal.get("release")
        if (type(release) is not dict or release.get("verified") is not True
                or release.get("intent_token") not in (None, accepted["intent_token"])
                or any(release.get(field) != [] for field in
                       ("keys_down", "buttons_down", "keys_unknown", "key_state_errors"))):
            raise ValueError("previous cover release is unverified")
        source = backend.cover_renewal_source(command["expected_sequence"])
        digest = accepted.get("program_sha256")
        if (type(terminal.get("input_owner_generation")) is not int
                or terminal["input_owner_generation"] != source["input_owner_generation"]
                or terminal.get("input_owner_id") != source["renewal_owner_id"]
                or type(digest) is not str or not DIGEST.fullmatch(digest)):
            raise ValueError("previous cover owner or program binding changed")
        target = release.get("target_process_identity")
        if target is not None and (type(target) is not list or len(target) != 4
                or target[1:3] != [source["target_process_identity"]["surface"],
                                   source["target_process_identity"]["digest"]]):
            raise ValueError("previous cover release targeted a different process")
        return dict(source, previous_program_sha256=digest)
    finally:
        executor.lock.release()


class PassiveProbeDelivery:
    """Own one read-only worker; stopping never joins its possibly blocked X I/O."""
    def __init__(self, check_source, capture, emit):
        self.check_source = check_source
        self.capture = capture
        self.emit = emit
        self.stop = threading.Event()
        self.worker = None
        self._lock = threading.Lock()
        self._approval = None

    def cancel(self):
        self.stop.set()
        with self._lock:
            self._approval = None

    def consume(self, command):
        with self._lock:
            approval, self._approval = self._approval, None
            if (approval is None or self.stop.is_set()
                    or command.get("id") != approval["request"]["id"]
                    or command.get("renewal_approval") != approval["nonce"]
                    or type(command.get("expected_sequence")) is not int
                    or command["expected_sequence"] != approval["request"]["expected_sequence"]
                    or type(command.get("steps")) is not list
                    or program_sha256(command["steps"]) != approval["source"]["previous_program_sha256"]
                    or time.perf_counter_ns() >= approval["request"]["deadline_ns"]
                    or not _same_exact_json_value(self.check_source(approval["request"]), approval["source"])):
                raise ValueError("renewal proof absent, stale, changed or already consumed")
            return approval["request"]["deadline_ns"]

    def start(self, command):
        if self.worker is not None and self.worker.is_alive():
            raise ValueError("one passive renewal probe may be pending")
        if (set(command) != {"op", "id", "previous_cover_id", "previous_intent_token",
                             "expected_sequence", "deadline_ns"}
                or type(command["id"]) is not str or not IDENTIFIER.fullmatch(command["id"])
                or type(command["previous_cover_id"]) is not str
                or type(command["previous_intent_token"]) is not str or not command["previous_intent_token"]
                or type(command["deadline_ns"]) is not int
                or not 0 < command["deadline_ns"] - time.perf_counter_ns() <= PROBE_NS):
            raise ValueError("exact passive renewal request required")
        self.cancel()
        stop = threading.Event()
        self.stop = stop
        identifier = command["id"]
        source = self.check_source(command)

        def observe():
            try:
                previous = {"id": command["previous_cover_id"], "intent_token": command["previous_intent_token"]}
                row = self.capture(identifier, previous, source, command["deadline_ns"], stop.is_set)
                if not _same_exact_json_value(source, self.check_source(command)):
                    raise ValueError("source changed while passive capture was pending")
                nonce = secrets.token_hex(16)
                with self._lock:
                    if stop.is_set() or time.perf_counter_ns() >= command["deadline_ns"]:
                        return
                    self._approval = {"request": dict(command), "source": source, "nonce": nonce}
                row = dict(row, approval_nonce=nonce)
            except Exception as error:
                row = {"event": "cover_renewal_passive_refused", "id": identifier,
                       "reason": type(error).__name__, "grants_input_authority": False}
            if not stop.is_set() and time.perf_counter_ns() < command["deadline_ns"]:
                self.emit(row)

        self.worker = threading.Thread(target=observe, name="cover-renewal-witness", daemon=True)
        self.worker.start()
