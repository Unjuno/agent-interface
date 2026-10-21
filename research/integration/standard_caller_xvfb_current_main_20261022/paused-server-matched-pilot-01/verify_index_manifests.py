from pathlib import Path
import hashlib
import subprocess


base = Path("research/integration/standard_caller_xvfb_current_main_20261022/paused-server-matched-pilot-01")
manifests = []
for manifest, prefix in ((base / "SHA256SUMS.txt", base),
                         (base / "raw" / "SHA256SUMS.txt", base / "raw")):
    for line in manifest.read_text().splitlines():
        expected, relative = line.split("  ", 1)
        manifests.append((expected, (prefix / relative).as_posix()))

index_output = subprocess.check_output(
    ["git", "ls-files", "-s", "--", base.as_posix()], text=True)
index = {}
for line in index_output.splitlines():
    _mode, oid, _stage, name = line.split(None, 3)
    index[name] = oid

missing = [name for _expected, name in manifests if name not in index]
if missing:
    raise SystemExit(f"manifest entries absent from Git index: {missing}")

oids = list(dict.fromkeys(index[name] for _expected, name in manifests))
stream = subprocess.check_output(
    ["git", "cat-file", "--batch"], input=("\n".join(oids) + "\n").encode())
blobs = {}
offset = 0
for requested_oid in oids:
    end = stream.index(b"\n", offset)
    oid, kind, size_text = stream[offset:end].decode().split()
    size = int(size_text)
    offset = end + 1
    data = stream[offset:offset + size]
    if oid != requested_oid or kind != "blob" or len(data) != size:
        raise SystemExit(f"invalid cat-file response for {requested_oid}")
    blobs[oid] = hashlib.sha256(data).hexdigest()
    offset += size
    if stream[offset:offset + 1] != b"\n":
        raise SystemExit(f"missing cat-file separator after {requested_oid}")
    offset += 1

bad = [(name, expected, blobs[index[name]])
       for expected, name in manifests if blobs[index[name]] != expected]
print({"manifest_entries": len(manifests), "index_blob_mismatches": bad})
if bad:
    raise SystemExit(1)
