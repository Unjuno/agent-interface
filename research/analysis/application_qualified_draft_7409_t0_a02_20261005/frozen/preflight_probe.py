"""Verify read-only source and distinct writable output mounts before A02."""
import json
from pathlib import Path


source = Path("/src/cases.json")
output = Path("/out/mount_probe.txt")
read_ok = bool(source.read_bytes())
write_rejected = False
try:
    Path("/src/.write_probe").write_text("must-not-exist", encoding="utf-8")
except OSError:
    write_rejected = True
output.write_text("writable-output-ok\n", encoding="utf-8")
output_ok = output.read_text(encoding="utf-8").strip() == "writable-output-ok"
result = {"source_read": read_ok, "source_write_rejected": write_rejected, "output_write_readback": output_ok}
print(json.dumps(result, sort_keys=True))
if not all(result.values()):
    raise SystemExit(1)
