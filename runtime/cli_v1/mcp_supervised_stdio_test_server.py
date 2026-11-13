"""Test-only stdio server for expiry/recovery protocol integration tests."""
import argparse
import json
import time
from pathlib import Path

from runtime.cli_v1.mcp_server import create_server
from runtime.cli_v1.test_mcp_supervised_win32 import (
    DelayedRecoveringFakeSupervisor,
    FakeProcess,
    GENERATION,
    HeldProducerFactory,
)
from runtime.cli_v1.owned_win32_session import OwnedWin32SessionOwner
from runtime.guarded_win32_v1.operation_owner import OperationOwner


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--effect", choices=("success", "failure"), default="failure")
    args = parser.parse_args()
    process = FakeProcess()
    identity = {"pid": 7101, "creation_time_100ns": 90101}
    operation_owner = OperationOwner(clock_ns=time.monotonic_ns,
        process_identity_reader=lambda handle: identity if handle is process else None)
    supervisor = DelayedRecoveringFakeSupervisor(operation_owner, process)
    owner = OwnedWin32SessionOwner(operation_owner, supervisor,
        synthetic_only=False)
    owner.bind_target_generation_reader(lambda: GENERATION)
    producer = HeldProducerFactory(process, identity)
    producer.program_actions_lower_bound = 2

    def oracle(action):
        return {"call_id": action["call_id"],
            "operation_id": action["operation_id"],
            "target_generation": action["target_generation"],
            "oracle_id": "f" * 32, "outcome": args.effect,
            "observed_monotonic_ns": time.monotonic_ns(),
            "evidence_ref": "stdio-fake-oracle:delayed-expiry"}

    server = create_server({"fixture": 123}, args.output_directory,
        session_mode="supervised-win32",
        _supervised_win32_owner_factory=lambda *_args: owner,
        _supervised_win32_producer_factory=lambda *_args: producer,
        supervised_win32_task_oracle=oracle)
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
