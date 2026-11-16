"""Test-only stdio server for expiry/recovery protocol integration tests."""
import argparse
import hashlib
import json
import sys
import threading
import time
from pathlib import Path

from runtime.cli_v1.mcp_server import create_server
from runtime.cli_v1.test_mcp_supervised_win32 import (
    AbruptExitProducerFactory,
    DelayedRecoveringFakeSupervisor,
    ExceptionReceiptProducerFactory,
    FakeProducerFactory,
    FakeProcess,
    FakeSupervisor,
    GENERATION,
    HeldProducerFactory,
    RecoveringFakeSupervisor,
    UnknownAfterCancelSupervisor,
)
from runtime.cli_v1.owned_win32_session import OwnedWin32SessionOwner
from runtime.guarded_win32_v1.operation_owner import OperationOwner


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--targets", type=Path)
    parser.add_argument("--production-cli", action="store_true",
        help="Run the production mcp_server.main parser/stdio entrypoint with fake owners.")
    parser.add_argument("--mode", choices=("delayed-expiry", "exception",
        "abrupt-exit",
        "exception-unknown", "recovery", "authority-expiry"),
        default="delayed-expiry")
    parser.add_argument("--public-caller", action="store_true",
        help="Enable the opt-in expiry caller policy for stdio protocol tests.")
    parser.add_argument("--deadline-cancel-grace-ms", type=int, default=1000)
    parser.add_argument("--recovery-generation", default="b" * 64)
    parser.add_argument("--recovery-result-delay-ms", type=int, default=0,
        help="test-only delay after a completed recovery horizon and before its terminal receipt returns")
    parser.add_argument("--recovery-invalid-horizon", action="store_true",
        help="test-only: return a recovery receipt whose sample count cannot cover its claimed horizon")
    parser.add_argument("--native-button-receipt", action="store_true",
        help="test-only: retain a native mouse button-up receipt")
    parser.add_argument("--recovery-foreground-refused", action="store_true",
        help="test-only: run the production recovery helper with an unrelated foreground receiver")
    parser.add_argument("--recovery-focus-drift", action="store_true",
        help="test-only: lose the foreground receiver after the initial recovery gate")
    parser.add_argument("--oracle-success", action="store_true",
        help="Return a positive fake task-oracle receipt for caller integration tests.")
    parser.add_argument("--oracle-delay-ms", type=int, default=0,
        help="Test-only delay before the fake task oracle returns its receipt.")
    args = parser.parse_args()
    if not 0 <= args.recovery_result_delay_ms <= 10000:
        parser.error("--recovery-result-delay-ms must be in [0, 10000]")
    if not 0 <= args.oracle_delay_ms <= 10000:
        parser.error("--oracle-delay-ms must be in [0, 10000]")
    process = FakeProcess()
    identity = {"pid": 7101, "creation_time_100ns": 90101}
    operation_owner = OperationOwner(clock_ns=time.monotonic_ns,
        process_identity_reader=lambda handle: identity if handle is process else None)
    if args.mode == "recovery":
        supervisor = FakeSupervisor(operation_owner)
        def recover(operation_id, generation, recovery_id, deadline_ns,
                    obligations, *, recovery_target_generation=None):
            if args.recovery_foreground_refused or args.recovery_focus_drift:
                from runtime.cli_v1.win32_supervisor_helpers import _recover
                recovery_generation = (recovery_target_generation
                    or args.recovery_generation)
                class ForegroundDeniedBackend:
                    def __init__(self, targets):
                        self.targets = targets
                        self.foreground_checks = 0
                        self.held_keys = {}
                        self.held_key_encodings = {}
                        self.held_key_targets = {}
                        self.held_buttons = set()
                        self.held_button_targets = {}
                        self.pending_unicode_ups = set()
                        self.key_up_calls = []
                    def target_generation(self, target):
                        if target not in self.targets:
                            raise RuntimeError("unknown target")
                        return recovery_generation
                    def _require_foreground(self, _target):
                        self.foreground_checks += 1
                        if (args.recovery_foreground_refused
                                or (args.recovery_focus_drift
                                    and self.foreground_checks >= 2)):
                            raise RuntimeError("foreground focus changed")
                    def _send_key(self, vk, down, encoding=None):
                        self.key_up_calls.append((vk, down, encoding))
                    def release_all(self):
                        for key, vk in list(self.held_keys.items()):
                            self._send_key(vk, False,
                                self.held_key_encodings.get(key))
                        return {"verified": True, "keys_down": [],
                            "buttons_down": [], "keys_unknown": [],
                            "buttons_unknown": []}
                    def close(self):
                        return None
                try:
                    return _recover({
                        "operation_id": operation_id,
                        "source_target_generation": generation,
                        "target_generation": recovery_generation,
                        "recovery_id": recovery_id,
                        "deadline_ns": deadline_ns,
                        "focus_target_before_release": False,
                        "obligations": obligations},
                        backend_factory=ForegroundDeniedBackend,
                        configured_targets={"fixture": 123})
                except RuntimeError as error:
                    return {"status": "unknown", "reason": str(error),
                        "operation_id": operation_id,
                        "source_target_generation": generation,
                        "target_generation": recovery_generation,
                        "recovery_target_generation": recovery_generation,
                        "recovery_id": recovery_id,
                        "release_confirmed": False}
            released_ns = time.monotonic_ns()
            sample_times = []
            for index in range(22):
                sample_times.append(time.monotonic_ns())
                if index < 21:
                    time.sleep(0.1)
            observed_end_ns = sample_times[-1]
            max_sample_gap_ns = max(
                later - earlier
                for earlier, later in zip(sample_times, sample_times[1:]))
            receipt = {"status": "recovered", "release_confirmed": True,
                "operation_id": operation_id,
                "target_generation": recovery_target_generation,
                "source_target_generation": generation,
                "recovery_target_generation": recovery_target_generation,
                "recovery_id": recovery_id, "readback": {"neutral": True},
                "late_input_horizon_verified": True,
                "late_input_horizon_ns": 2_000_000_000,
                "late_input_release_received_monotonic_ns": released_ns,
                "late_input_observation_start_monotonic_ns": sample_times[0],
                "late_input_observation_end_monotonic_ns": observed_end_ns,
                "late_input_observation_count": len(sample_times),
                "late_input_max_observed_gap_ns": max_sample_gap_ns,
                "late_input_max_sample_gap_ns": max_sample_gap_ns}
            if args.recovery_invalid_horizon:
                receipt["late_input_observation_count"] = 1
            if args.recovery_result_delay_ms:
                time.sleep(args.recovery_result_delay_ms / 1000)
            return receipt
        supervisor.recover_orphaned_input = recover
        target_generation = args.recovery_generation
    elif args.mode == "delayed-expiry":
        supervisor = DelayedRecoveringFakeSupervisor(operation_owner, process)
        target_generation = GENERATION
    elif args.mode == "exception":
        supervisor = RecoveringFakeSupervisor(operation_owner, process,
            native_button_receipt=args.native_button_receipt)
        target_generation = GENERATION
    elif args.mode == "exception-unknown":
        supervisor = UnknownAfterCancelSupervisor(operation_owner)
        target_generation = GENERATION
    elif args.mode == "authority-expiry":
        supervisor = FakeSupervisor(operation_owner)
        target_generation = GENERATION
    elif args.mode == "abrupt-exit":
        supervisor = RecoveringFakeSupervisor(operation_owner, process)
        target_generation = GENERATION
    else:
        supervisor = FakeSupervisor(operation_owner)
        target_generation = GENERATION
    owner = OwnedWin32SessionOwner(operation_owner, supervisor,
        synthetic_only=False)
    owner.bind_target_generation_reader(lambda: target_generation)
    if args.mode == "authority-expiry":
        from runtime.backends.win32_v1.backend import Win32Backend
        from runtime.backends.win32_v1.session import Win32RuntimeSession

        class ExactObligationRecoverySupervisor(RecoveringFakeSupervisor):
            """Test adapter that records releases for the frozen obligations."""
            def cancel(self, operation_id, generation, *, cleanup_deadline_ns):
                self.operation_owner.request_cancel(operation_id, generation,
                    cleanup_deadline_ns=cleanup_deadline_ns)
                if self.process.alive:
                    remaining_ns = max(0,
                        cleanup_deadline_ns - time.monotonic_ns())
                    self.process.join(remaining_ns / 1_000_000_000)
                if self.process.is_alive():
                    raise AssertionError(
                        "fake producer did not retire within cleanup deadline")
                if not self.operation_owner.producer_retired(
                        operation_id, generation, self.process):
                    raise AssertionError("fake producer retirement was not accepted")
                recovery = self.operation_owner.claim_recovery(
                    operation_id, generation)
                if recovery is None:
                    raise AssertionError("fake recovery was not admitted")
                key_codes = {"SHIFT": 0x10, "CTRL": 0x11}
                key_attempts = []
                for obligation in recovery["obligations"]:
                    kind, _target, key, encoding = obligation.split(":", 3)
                    if kind != "key" or key not in key_codes:
                        raise AssertionError("unexpected frozen obligation")
                    key_attempts.append({"virtual_key": key_codes[key],
                        "encoding": encoding, "status": "returned"})
                readback = {"operation_id": operation_id,
                    "target_generation": generation,
                    "recovery_id": recovery["recovery_id"], "neutral": True,
                    "observed_monotonic_ns": time.monotonic_ns(),
                    "key_button_states": [False] * len(recovery["obligations"]),
                    "unicode_event_units": 0}
                self.operation_owner.recovery_release_attempted(operation_id,
                    generation, recovery["recovery_id"], key_attempts)
                if not self.operation_owner.recovery_completed(operation_id,
                        generation, recovery["recovery_id"],
                        release_accepted=True, readback=readback):
                    raise AssertionError("exact-obligation fake recovery failed")
                (args.output_directory / "authority-expiry-recovery.json").write_text(
                    json.dumps({"obligations": recovery["obligations"],
                        "key_up_attempts": key_attempts,
                        "readback": readback}, sort_keys=True), encoding="utf-8")
                return self.operation_owner.result(operation_id)

        class ThreadedFakeProcess:
            def __init__(self):
                self.pid = None
                self.exitcode = None
                self.alive = False
                self.start_gate = threading.Event()
                self.run_program = None
                self.result = None
                self.events = None
                self.program_emissions = 0
                self.program_started_monotonic_ns = None
                self._thread = None

            def start(self):
                self.pid = identity["pid"]
                self.alive = True
                self._thread = threading.Thread(target=self._child, daemon=True)
                self._thread.start()

            def _child(self):
                try:
                    if not self.start_gate.wait(5):
                        self.exitcode = 86
                        return
                    self.run_program()
                    self.exitcode = 0
                except BaseException:
                    self.exitcode = 87
                finally:
                    self.alive = False

            def is_alive(self):
                return self.alive

            def join(self, timeout=None):
                if self._thread is not None:
                    self._thread.join(timeout)

            def close(self):
                return None

        process = ThreadedFakeProcess()
        supervisor = ExactObligationRecoverySupervisor(operation_owner, process)
        owner._supervisor = supervisor

        class ExpiredProgramProducerFactory:
            def __init__(self):
                self.process = process

            def __call__(self, action):
                def run_program():
                    process.program_started_monotonic_ns = time.monotonic_ns()
                    backend = Win32Backend.__new__(Win32Backend)
                    backend.emissions = 0
                    backend._program_emission_counter = None
                    backend.held_keys = {}
                    backend.held_buttons = set()
                    backend.pending_unicode_ups = set()
                    backend.manifest = lambda: Win32Backend.manifest(backend)
                    backend.monotonic_ns = time.monotonic_ns
                    backend.preflight = lambda _program: None
                    backend.targets = {"fixture": 123}
                    backend.target_generation = lambda _target: GENERATION
                    backend.monotonic_ns = time.monotonic_ns
                    backend.user32 = type("User32", (), {
                        "IsWindow": staticmethod(lambda hwnd: hwnd == 123),
                        "GetForegroundWindow": staticmethod(lambda: 123),
                        "SendInput": staticmethod(lambda *_args: 1),
                    })()
                    events = []
                    backend.focus = lambda target: events.append(("focus", target))

                    def key_state(key, down, **_kwargs):
                        if down:
                            events.append(("down", key))
                            backend._record_emission()
                            backend.held_keys[key] = 0x10
                        else:
                            events.append(("up", key))
                            backend.held_keys.pop(key, None)

                    backend.key_state = key_state

                    def release_all():
                        events.append(("release_all",
                            tuple(sorted(backend.held_keys))))
                        for key in list(backend.held_keys):
                            key_state(key, False)
                        return {"verified": True, "keys_down": [],
                            "buttons_down": [], "keys_unknown": [],
                            "buttons_unknown": []}

                    backend.release_all = release_all
                    session = Win32RuntimeSession(backend)
                    result = session.dispatch(action["program"],
                        current_observation_seq=action["program"]["source"][
                            "observation_seq"],
                        current_binding_revision=action["program"]["source"][
                            "binding_revision"])
                    process.result = result
                    process.events = events
                    process.program_emissions = result.get("program_emissions", 0)
                    args.output_directory.mkdir(parents=True, exist_ok=True)
                    (args.output_directory / "authority-expiry-events.json").write_text(
                        json.dumps({"events": events,
                            "result_status": result.get("status"),
                            "error": result.get("detail"),
                            "program_emissions": process.program_emissions,
                            "program_started_monotonic_ns":
                                process.program_started_monotonic_ns},
                            sort_keys=True), encoding="utf-8")

                process.run_program = run_program
                process.result = None
                process.events = None
                process.program_emissions = 0
                process.start_gate.clear()
                return (process,
                    lambda: identity,
                    process.start_gate.set)

            def read_result(self, handle):
                if handle is not process or handle.is_alive():
                    raise RuntimeError("expired producer has not completed")
                return {"result": handle.result,
                    "release_receipt": handle.result.get("release")}

            def read_program_actions_lower_bound(self, handle):
                if handle is not process:
                    raise ValueError("unknown expired producer")
                return handle.program_emissions

        producer = ExpiredProgramProducerFactory()
    if args.mode == "authority-expiry":
        pass
    elif args.mode == "recovery":
        producer = FakeProducerFactory(process, identity)
    elif args.mode in ("exception", "exception-unknown"):
        producer = ExceptionReceiptProducerFactory(process, identity)
    elif args.mode == "abrupt-exit":
        producer = AbruptExitProducerFactory(process, identity)
    else:
        producer = HeldProducerFactory(process, identity)
        producer.program_actions_lower_bound = 2

    def oracle(action):
        if args.oracle_delay_ms:
            time.sleep(args.oracle_delay_ms / 1000)
        oracle_receipt={"call_id": action["call_id"],
            "operation_id": action["operation_id"],
            "target_generation": action["target_generation"],
            "oracle_id": "f" * 32,
            "outcome": "success" if args.oracle_success else "failure",
            "observed_monotonic_ns": time.monotonic_ns(),
            "evidence_ref": "stdio-fake-oracle:delayed-expiry"}
        args.output_directory.mkdir(parents=True, exist_ok=True)
        with (args.output_directory / "oracle-call-ids.jsonl").open(
                "a", encoding="utf-8") as stream:
            stream.write(json.dumps({"call_id":action["call_id"],
                "operation_id":action["operation_id"],
                "outcome":oracle_receipt["outcome"],
                "response_sha256":hashlib.sha256(json.dumps(oracle_receipt,
                    sort_keys=True,separators=(",", ":"),allow_nan=False
                    ).encode("utf-8")).hexdigest(),
                "observed_monotonic_ns":oracle_receipt[
                    "observed_monotonic_ns"]},
                sort_keys=True, allow_nan=False)+"\n")
        return oracle_receipt

    if args.production_cli:
        if args.targets is None:
            parser.error("--production-cli requires --targets")
        from runtime.cli_v1 import mcp_server
        real_create_server = mcp_server.create_server

        def create_fake_backed_server(targets, output_directory, **options):
            return real_create_server(targets, output_directory,
                _supervised_win32_owner_factory=lambda *_args: owner,
                _supervised_win32_producer_factory=lambda *_args: producer,
                supervised_win32_task_oracle=oracle,
                **options)

        mcp_server.create_server = create_fake_backed_server
        sys.argv = ["mcp_server", "--targets", str(args.targets),
            "--output-directory", str(args.output_directory),
            "--session-mode", "supervised-win32"]
        if args.public_caller:
            sys.argv.extend([
                "--supervised-win32-deadline-cancel-policy", "public-caller",
                "--supervised-win32-deadline-cancel-grace-ms",
                str(args.deadline_cancel_grace_ms)])
        mcp_server.main()
        return

    server_options = {}
    if args.public_caller:
        if not 1 <= args.deadline_cancel_grace_ms <= 2000:
            parser.error("--deadline-cancel-grace-ms must be in [1, 2000]")
        server_options.update(
            _supervised_win32_deadline_cancel_policy="public_caller",
            _supervised_win32_deadline_cancel_grace_ns=(
                args.deadline_cancel_grace_ms * 1_000_000))
    server = create_server({"fixture": 123}, args.output_directory,
        session_mode="supervised-win32",
        _supervised_win32_owner_factory=lambda *_args: owner,
        _supervised_win32_producer_factory=lambda *_args: producer,
        supervised_win32_task_oracle=oracle,
        **server_options)
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
