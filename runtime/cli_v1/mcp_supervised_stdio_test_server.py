"""Test-only stdio server for expiry/recovery protocol integration tests."""
import argparse
import json
import time
from pathlib import Path

from runtime.cli_v1.mcp_server import create_server
from runtime.cli_v1.test_mcp_supervised_win32 import (
    DelayedRecoveringFakeSupervisor,
    ExceptionReceiptProducerFactory,
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
    parser.add_argument("--mode", choices=("delayed-expiry", "exception",
        "exception-unknown", "recovery"),
        default="delayed-expiry")
    parser.add_argument("--public-caller", action="store_true",
        help="Enable the opt-in expiry caller policy for stdio protocol tests.")
    parser.add_argument("--deadline-cancel-grace-ms", type=int, default=1000)
    parser.add_argument("--recovery-generation", default="b" * 64)
    args = parser.parse_args()
    process = FakeProcess()
    identity = {"pid": 7101, "creation_time_100ns": 90101}
    operation_owner = OperationOwner(clock_ns=time.monotonic_ns,
        process_identity_reader=lambda handle: identity if handle is process else None)
    if args.mode == "recovery":
        supervisor = FakeSupervisor(operation_owner)
        def recover(operation_id, generation, recovery_id, deadline_ns,
                    obligations, *, recovery_target_generation=None):
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
            return {"status": "recovered", "release_confirmed": True,
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
        supervisor.recover_orphaned_input = recover
        target_generation = args.recovery_generation
    elif args.mode == "delayed-expiry":
        supervisor = DelayedRecoveringFakeSupervisor(operation_owner, process)
        target_generation = GENERATION
    elif args.mode == "exception":
        supervisor = RecoveringFakeSupervisor(operation_owner, process)
        target_generation = GENERATION
    elif args.mode == "exception-unknown":
        supervisor = UnknownAfterCancelSupervisor(operation_owner)
        target_generation = GENERATION
    else:
        supervisor = FakeSupervisor(operation_owner)
        target_generation = GENERATION
    owner = OwnedWin32SessionOwner(operation_owner, supervisor,
        synthetic_only=False)
    owner.bind_target_generation_reader(lambda: target_generation)
    if args.mode in ("exception", "exception-unknown"):
        producer = ExceptionReceiptProducerFactory(process, identity)
    else:
        producer = HeldProducerFactory(process, identity)
        producer.program_actions_lower_bound = 2

    def oracle(action):
        return {"call_id": action["call_id"],
            "operation_id": action["operation_id"],
            "target_generation": action["target_generation"],
            "oracle_id": "f" * 32, "outcome": "failure",
            "observed_monotonic_ns": time.monotonic_ns(),
            "evidence_ref": "stdio-fake-oracle:delayed-expiry"}

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
