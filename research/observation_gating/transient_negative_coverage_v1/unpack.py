"""Verify and unpack Issue 3948 without launching a server or executable."""
import base64
import hashlib
import io
import json
import pathlib
import sys
import tarfile

HERE = pathlib.Path(__file__).resolve().parent
ARCHIVES = (
    (["SOURCE.01.b64", "SOURCE.02.b64", "SOURCE.03.b64"],
     "76363f0aceab7166b3faee12f781a766c9259230a7bb20ae1028a281a45a7879"),
    (["RESULT.b64"],
     "fd23264b1ec704267db9ebb9aebae5625d7f650feb25e74bde151e85d413b955"),
)

def digest(data):
    return hashlib.sha256(data).hexdigest()

def unpack(destination):
    destination.mkdir(parents=True, exist_ok=False)
    total = 0
    for names, expected in ARCHIVES:
        encoded = "".join((HERE / name).read_text().strip() for name in names)
        data = base64.b64decode(encoded, validate=True)
        if digest(data) != expected:
            raise ValueError("Archive hash mismatch: " + names[0])
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:xz") as archive:
            for member in archive:
                path = pathlib.PurePosixPath(member.name)
                if not member.isfile() or path.is_absolute() or ".." in path.parts:
                    raise ValueError("Unsafe archive member: " + member.name)
                total += member.size
                if total > 2_000_000:
                    raise ValueError("Expanded-size limit exceeded")
                target = destination.joinpath(*path.parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                source = archive.extractfile(member)
                if source is None:
                    raise ValueError("Missing member data")
                with target.open("xb") as output:
                    output.write(source.read())
                # Extraction intentionally grants no executable permission.
    freeze = json.loads((destination / "FREEZE.json").read_text())
    for name, expected in freeze["sources"].items():
        if digest((destination / name).read_bytes()) != expected:
            raise ValueError("Frozen source mismatch: " + name)
    checks = {
        "FREEZE.json": "65a33351f5d1e8588cc3e5912e7e334341762ed50fd9d91ab7fe98693dd20454",
        "formal-01/RAW.json": "fc7a15404728cf501e3a91e60a13ed123737bf71d5b16c7bb60489a7d8858c8c",
    }
    for name, expected in checks.items():
        if digest((destination / name).read_bytes()) != expected:
            raise ValueError("Evidence mismatch: " + name)
    if (destination / "policy.py").read_bytes() != (HERE / "policy.py").read_bytes():
        raise ValueError("Reviewable policy differs from frozen source")
    print(json.dumps({"verified": True, "destination": str(destination),
                      "files": sum(p.is_file() for p in destination.rglob("*")),
                      "expanded_bytes": total}, sort_keys=True))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python unpack.py NEW_EMPTY_DESTINATION")
    unpack(pathlib.Path(sys.argv[1]).resolve())
