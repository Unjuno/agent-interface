import hashlib, io, json, lzma, tarfile
from pathlib import Path

EXPECTED = "7fe175f9b4983dd21767745c6b23efc4405938ee48652ea15421d17ca8c35a2f"
MANIFEST = "MANIFEST.json"


def main():
    manifest = json.loads(Path(MANIFEST).read_text())
    for item in manifest["files"]:
        data = Path(item["path"]).read_bytes()
        if len(data) != item["bytes"] or hashlib.sha256(data).hexdigest() != item["sha256"]:
            raise SystemExit("manifest mismatch: " + item["path"])
    files = [item["path"] for item in manifest["files"]] + [MANIFEST]
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w", format=tarfile.PAX_FORMAT) as tf:
        for name in sorted(files):
            data = Path(name).read_bytes()
            info = tarfile.TarInfo(name)
            info.size = len(data)
            info.mtime = 0
            info.uid = 0
            info.gid = 0
            info.uname = ""
            info.gname = ""
            info.mode = 0o644
            tf.addfile(info, io.BytesIO(data))
    archive = lzma.compress(buffer.getvalue(), format=lzma.FORMAT_XZ, preset=9 | lzma.PRESET_EXTREME)
    got = hashlib.sha256(archive).hexdigest()
    if got != EXPECTED:
        raise SystemExit(f"archive SHA mismatch: {got}")
    Path("route_decision_cost_v3_evidence.tar.xz").write_bytes(archive)
    print(f"PASS_RECONSTRUCT {len(archive)} {got}")


if __name__ == "__main__":
    main()
