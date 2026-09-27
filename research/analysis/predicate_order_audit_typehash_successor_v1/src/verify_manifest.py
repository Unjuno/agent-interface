import hashlib
import json
import sys
from pathlib import Path


def reject(message):
    print("REJECT " + message)
    raise SystemExit(2)


manifest_arg, root_arg = sys.argv[1:3]
manifest = json.loads(sys.stdin.read()) if manifest_arg == "-" else json.loads(Path(manifest_arg).read_text())
root = Path(root_arg)
required = manifest.get("required_paths")
if not isinstance(required, list) or not required or len(set(required)) != len(required):
    reject("required_paths")
for section in ("source_sha256", "input_sha256", "output_sha256"):
    values = manifest.get(section)
    if not isinstance(values, dict) or not values:
        reject("empty_" + section)
combined = {}
for section in ("source_sha256", "input_sha256", "output_sha256"):
    for key, digest in manifest[section].items():
        if key in combined or not isinstance(digest, str) or len(digest) != 64:
            reject("entry_" + key)
        combined[key] = digest
if set(combined) != set(required):
    reject("path_set")
for relative, expected in combined.items():
    path = root / relative.lstrip("/")
    try:
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        reject("missing_" + relative)
    if actual != expected:
        reject("digest_" + relative)
print("PASS_MANIFEST_EXACT_PATHS " + str(len(combined)))
