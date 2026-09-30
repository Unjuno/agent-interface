"""Restore retained data only. Does not execute any restored source."""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import lzma
from pathlib import Path, PurePosixPath
import tarfile

MAX_ARCHIVE = 1_000_000
MAX_EXPANDED = 8_000_000
MAX_FILES = 100


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def unpack(source: Path, destination: Path):
    # Source and destination parent are caller-controlled, trusted, quiescent paths.
    require(not destination.exists(), "destination must not exist")
    require(destination.parent.is_dir(), "destination parent missing")
    pack = json.loads((source / "PACK.json").read_bytes())
    for key, limit in (("archive_bytes", MAX_ARCHIVE), ("expanded_tar_bytes", MAX_EXPANDED),
                       ("member_bytes", MAX_EXPANDED), ("files", MAX_FILES)):
        require(type(pack[key]) is int and 0 < pack[key] <= limit, "invalid bound: " + key)
    parts = pack["parts"]
    require(type(parts) is list and 0 < len(parts) <= 32, "invalid parts")
    buffers = []
    for index, part in enumerate(parts):
        require(part["name"] == f"evidence-{index:02d}.xz.part", "part order/name")
        path = source / part["name"]
        require(path.is_file() and not path.is_symlink(), "part not regular")
        require(type(part["bytes"]) is int and 0 < part["bytes"] <= MAX_ARCHIVE,
                "part size bound")
        require(path.stat().st_size == part["bytes"], "part size")
        data = path.read_bytes()
        require(sha(data) == part["sha256"], "part digest")
        buffers.append(data)
    archive = b"".join(buffers)
    require(len(archive) == pack["archive_bytes"] and sha(archive) == pack["archive_sha256"],
            "archive identity")
    decoder = lzma.LZMADecompressor(memlimit=64 * 1024 * 1024)
    expanded = decoder.decompress(archive, max_length=pack["expanded_tar_bytes"] + 1)
    require(decoder.eof and not decoder.unused_data, "incomplete or trailing archive")
    require(len(expanded) == pack["expanded_tar_bytes"] and
            sha(expanded) == pack["expanded_tar_sha256"], "expanded identity")
    payloads = {}
    with tarfile.open(fileobj=io.BytesIO(expanded), mode="r:") as tar:
        for member in tar:
            name = member.name
            path = PurePosixPath(name)
            require(member.isfile() and not path.is_absolute() and ".." not in path.parts
                    and str(path) == name and "\\" not in name and name not in payloads,
                    "noncanonical member")
            require(type(member.size) is int and 0 <= member.size <= MAX_EXPANDED,
                    "member size")
            payloads[name] = tar.extractfile(member).read()
            require(len(payloads) <= MAX_FILES, "member count limit")
    require(len(payloads) == pack["files"] and
            sum(map(len, payloads.values())) == pack["member_bytes"], "member denominator")
    destination.mkdir(exist_ok=False)
    for name, data in payloads.items():
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as output:
            output.write(data)
    return {"files": len(payloads), "member_bytes": sum(map(len, payloads.values())),
            "archive_sha256": sha(archive)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    print(json.dumps(unpack(Path(__file__).resolve().parent, args.destination), sort_keys=True))
