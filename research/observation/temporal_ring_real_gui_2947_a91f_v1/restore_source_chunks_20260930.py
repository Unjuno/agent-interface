import base64
import hashlib
import io
import json
import pathlib
import sys
import tarfile


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def validated_members(root):
    recovery = json.loads((root / "RECOVERY_20260930.json").read_text())
    frozen = json.loads((root / "FREEZE.json").read_text())
    encoded_parts = []
    for part in recovery["parts"]:
        raw = (root / part["name"]).read_bytes()
        if len(raw) != part["bytes"] or sha256(raw) != part["sha256"]:
            raise ValueError("chunk identity mismatch: " + part["name"])
        encoded_parts.append(raw.strip())
    try:
        archive = base64.b64decode(b"".join(encoded_parts), validate=True)
    except ValueError as exc:
        raise ValueError("chunk concatenation is not strict base64") from exc
    if (len(archive) != recovery["archive_bytes"] or
            sha256(archive) != recovery["archive_sha256"]):
        raise ValueError("reconstructed archive identity mismatch")

    expected_sources = frozen["source_sha256"]
    expected_members = set(expected_sources) | {"FREEZE.json", "SOURCE_SHA256.json"}
    members = {}
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:xz") as tf:
        for info in tf.getmembers():
            path = pathlib.PurePosixPath(info.name)
            if (path.is_absolute() or len(path.parts) != 1 or
                    ".." in path.parts or "\\" in info.name or
                    not info.isfile() or info.issym() or info.islnk()):
                raise ValueError("unsafe or non-regular archive member: " + info.name)
            if info.name in members:
                raise ValueError("duplicate archive member: " + info.name)
            stream = tf.extractfile(info)
            if stream is None:
                raise ValueError("unreadable archive member: " + info.name)
            members[info.name] = stream.read()

    if set(members) != expected_members:
        raise ValueError("archive member set differs from frozen manifest")
    if members["FREEZE.json"] != (root / "FREEZE.json").read_bytes():
        raise ValueError("embedded FREEZE.json differs from committed freeze")
    embedded_hashes = json.loads(members["SOURCE_SHA256.json"])
    expected_hashes = dict(expected_sources)
    expected_hashes["FREEZE.json"] = sha256(members["FREEZE.json"])
    if embedded_hashes != expected_hashes:
        raise ValueError("embedded source hash manifest differs from freeze")
    for name, digest in expected_hashes.items():
        if sha256(members[name]) != digest:
            raise ValueError("frozen source hash mismatch: " + name)
    return archive, members


def restore(root, destination):
    if destination.exists():
        raise FileExistsError("destination already exists")
    archive, members = validated_members(root)
    destination.mkdir(parents=True)
    (destination / "temporal_ring_source.tar.xz").write_bytes(archive)
    for name, data in members.items():
        (destination / name).write_bytes(data)
    return sha256(archive), len(members)


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: restore_source_chunks_20260930.py DESTINATION")
    root = pathlib.Path(__file__).resolve().parent
    digest, count = restore(root, pathlib.Path(sys.argv[1]))
    print(json.dumps({"archive_sha256": digest, "restored_members": count},
                     sort_keys=True))


if __name__ == "__main__":
    main()
