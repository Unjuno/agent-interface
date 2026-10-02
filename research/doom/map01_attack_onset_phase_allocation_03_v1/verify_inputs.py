from __future__ import annotations

import argparse
import hashlib
import json
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE_CAPSULE_SHA256 = "317068daacc2abafacc44b85e18c0b1ad468fa8eb185361fd9cdf3b247475e9e"
SOURCE_SHA256 = {
    "audit.py": "d462b4cea332ed1e7dc658857de2ff6978f501f2445b142d9f525dc63d18242a",
    "construction.py": "1640b52852de5cf5764980234336693aad6c861c9f582268c8921f165b9b9a8e",
    "formal_runner.py": "86e92050d2e52bfaffd255e56f02e85366069004a4a7c0f728598a3e88fcfb11",
    "map01_v12_transition_owner.py": "3626281eb6066fa71e500160c671a3946c11fd7abb3a624d4f05d5cbed2f0db1",
    "run_case.py": "38bcced828837651732e126f8035f7685aaee380fd4f6b067e28be830974340a",
    "session_entry.py": "4489f83991311e17d9c6859f7d03f09943bc054854f90d92e72b24a880e155f9",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wheels", type=Path, required=True)
    parser.add_argument("--artifact-zip", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    manifest_path = ROOT / "inputs/runtime-artifact-manifest.json"
    manifest = json.loads(manifest_path.read_text())
    source_manifest = json.loads((ROOT / "dependencies/v12/SOURCE_MANIFEST.json").read_text())
    test_support = json.loads((ROOT / "test-support/SOURCE_MAP.json").read_text())
    with tarfile.open(ROOT / "inputs/runtime-source.tar.gz", "r:gz") as archive:
        source_members = {m.name.removeprefix("./"): m for m in archive.getmembers() if m.isfile()}

        def archived_sha(name: str) -> tuple[int, str]:
            member = source_members[name]
            stream = archive.extractfile(member)
            assert stream is not None
            digest = hashlib.sha256()
            size = 0
            while chunk := stream.read(1024 * 1024):
                size += len(chunk)
                digest.update(chunk)
            return size, digest.hexdigest()

        source_rows = {
            name: archived_sha(name) == (entry["bytes"], entry["sha256"])
            for name, entry in manifest["files"].items()
            if name in source_members
        }
        source_exact = (
            set(source_members) == set(manifest["files"])
            and len(source_rows) == len(manifest["files"])
            and all(source_rows.values())
        )

    v12_rows = {
        name: (ROOT / "dependencies/v12" / name).is_file()
        and sha(ROOT / "dependencies/v12" / name) == digest
        for name, digest in source_manifest["files"].items()
    }
    wheel_rows = {
        name: (args.wheels / Path(name).name).is_file()
        and sha(args.wheels / Path(name).name) == entry["sha256"]
        and (args.wheels / Path(name).name).stat().st_size == entry["bytes"]
        for name, entry in manifest["wheels"].items()
    }
    test_support_rows = {}
    for name, entry in test_support["files"].items():
        path = ROOT / "test-support" / name
        data = path.read_bytes() if path.is_file() else b""
        blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
        test_support_rows[name] = (
            path.is_file()
            and len(data) == entry["bytes"]
            and hashlib.sha256(data).hexdigest() == entry["sha256"]
            and blob == entry["git_blob"]
        )
    checks = {
        "allocation_source_capsule": sha(ROOT / "inputs/SOURCE.tar.xz") == SOURCE_CAPSULE_SHA256,
        "experiment_source_files": all(
            (ROOT / "source" / name).is_file() and sha(ROOT / "source" / name) == digest
            for name, digest in SOURCE_SHA256.items()
        ),
        "v12_dependency_manifest": all(v12_rows.values()),
        "runtime_source_commit": manifest["base_commit"] == "9e6d5ecdbb5440fd5df1883161f2c63b2c3bb245",
        "runtime_source_archive": source_exact,
        "offline_wheel_manifest": len(wheel_rows) == 12 and all(wheel_rows.values()),
        "comparison_test_support": all(test_support_rows.values()),
        "runtime_artifact_archive": args.artifact_zip is None
        or sha(args.artifact_zip)
        == "522763418610ea10e57e55615fa71e76445200b9f86d208820ea97c77c234f0b",
    }
    result = {
        "schema": "map01-attack-onset-allocation-03-input-verification-v1",
        "decision": "PASS_PREREGISTERED_INPUTS_ONLY" if all(checks.values()) else "FAIL_INPUT_IDENTITY",
        "checks": checks,
        "runtime_source_files": len(source_members),
        "runtime_wheels": len(wheel_rows),
        "v12_files": len(v12_rows),
        "test_support_files": len(test_support_rows),
        "scientific_sessions": 0,
        "formal_invocations": 0,
    }
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered)
    print(rendered, end="")
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
