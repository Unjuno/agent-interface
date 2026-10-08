"""Check the frozen source and distinct writable result mounts before allocation."""
import json
from pathlib import Path


source = Path("/src/cases.json")
output = Path("/out/mount_probe.txt")
source_bytes = source.read_bytes()
read_only_rejected_write = False
try:
    Path("/src/.write_probe").write_text("must-not-exist", encoding="utf-8")
except OSError:
    read_only_rejected_write = True
output.write_text("writable-output-ok\n", encoding="utf-8")
result = {
    "source_read": bool(source_bytes),
    "source_write_rejected": read_only_rejected_write,
    "output_write_readback": output.read_text(encoding="utf-8").strip() == "writable-output-ok",
}
print(json.dumps(result, sort_keys=True))
if not all(result.values()):
    raise SystemExit(1)
