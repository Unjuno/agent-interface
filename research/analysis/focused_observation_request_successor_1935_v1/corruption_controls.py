import hashlib
import json

def digest(obj):
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest(), raw

source = {"frame": "A1", "region": [1, 1, 2, 2], "pixels": [[2]]}
h, raw = digest(source)
controls = []
for key, value in [("frame", "B1"), ("region", [0, 0, 2, 2]), ("pixels", [[3]]), ("extra", True)]:
    altered = dict(source)
    altered[key] = value
    controls.append(digest(altered)[0] != h)
try:
    json.loads(raw[:-1])
    parsed = False
except json.JSONDecodeError:
    parsed = True
assert all(controls) and parsed
print({"tamper_controls": len(controls), "digest_changes": sum(controls), "truncation_rejected": parsed})
