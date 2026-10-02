"""Independent black-box contract audit for the Issue #59 gate candidate."""

import hashlib
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import gate


MANIFEST = {"commit": "733981dda72414c33d12c0687430989f12366db0", "files": {"runner.py": "a" * 64}}
MANIFEST_SHA = hashlib.sha256(json.dumps(MANIFEST, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
PAYLOAD = b'{"schema":"synthetic-v1","result":"ok"}'
IDLE = {"returncode": 0, "stdout": b""}
VALID = {"returncode": 0, "stdout": b'{"compute_processes":[]}'}


def run(inventory, output, candidate, patcher=None):
    if patcher is None:
        return gate.run_gated(inventory, MANIFEST, MANIFEST_SHA, candidate, output)
    with patcher:
        return gate.run_gated(inventory, MANIFEST, MANIFEST_SHA, candidate, output)


def main():
    checks = []
    with tempfile.TemporaryDirectory() as root:
        root = Path(root)

        calls = []
        output = root / "idle.json"
        result = run(IDLE, output, lambda: calls.append(1) or {"returncode": 0, "stdout": PAYLOAD})
        assert result["status"] == "ARTIFACT_PUBLISHED" and calls == [1]
        assert output.read_bytes() == PAYLOAD and result["raw_sha256"] == hashlib.sha256(PAYLOAD).hexdigest()
        checks.append("empty_inventory_is_idle_and_source_gated")

        for inventory, expected in (({"returncode": 0, "stdout": None}, "STOP_INVENTORY_OUTPUT_MISSING"),
                                    ({"returncode": 4, "stdout": b""}, "STOP_INVENTORY_COMMAND_FAILED"),
                                    ({"returncode": 0, "stdout": b'{"other":[]}'}, "STOP_INVENTORY_SCHEMA_INVALID")):
            calls = []
            result = run(inventory, root / f"{len(checks)}.json",
                         lambda: calls.append(1) or {"returncode": 0, "stdout": PAYLOAD})
            assert result["status"] == expected and result["candidate_invocations"] == 0 and not calls
            checks.append("fail_closed_" + expected.lower())

        output = root / "preserve.json"
        output.write_bytes(b"prior-owner")
        result = run(VALID, output, lambda: {"returncode": 0, "stdout": PAYLOAD})
        assert result["status"] == "STOP_OUTPUT_PATH_ALREADY_EXISTS" and output.read_bytes() == b"prior-owner"
        checks.append("existing_output_is_not_overwritten")

        output = root / "publish-denied.json"
        denied_link = patch.object(gate.os, "link", side_effect=PermissionError("audit fixture"))
        result = run(VALID, output, lambda: {"returncode": 0, "stdout": PAYLOAD}, denied_link)
        assert result["status"] == "STOP_OUTPUT_PUBLISH_FAILED" and result["raw_sha256"] is None and not output.exists()
        checks.append("publication_denial_is_typed_stop")

        output = root / "tampered.json"
        original_link = gate.os.link

        def tamper_after_link(source, destination):
            original_link(source, destination)
            Path(destination).write_bytes(b"tampered")

        tamper = patch.object(gate.os, "link", side_effect=tamper_after_link)
        result = run(VALID, output, lambda: {"returncode": 0, "stdout": PAYLOAD}, tamper)
        assert (result["status"], result["scientific_result"], result["raw_sha256"]) == (
            "STOP_POSTWRITE_DIGEST_MISMATCH", "NOT_EVALUATED", None)
        assert not output.exists()
        checks.append("postpublication_mismatch_has_no_artifact")

    print(json.dumps({"audit": "PASS_BOUNDED_CONTRACT", "checks": checks, "check_count": len(checks)},
                     sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
