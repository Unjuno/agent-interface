import base64
import hashlib
import os
import subprocess
import sys
from pathlib import Path

packet = Path(__file__).resolve().parent
package = packet.parents[1]
repo = packet.parents[4]
env = os.environ.copy()
env["PYTHONPATH"] = str(repo) + os.pathsep + str(package)
common = [
    "-m", "unittest", "test_effect_receipt_handoff_v1",
    "test_recorded_comparison_adapter_v1", "test_comparison_measurement_v1", "-v",
]
rows = []
for name, flags in (("normal", []), ("optimized", ["-O"])):
    command = [sys.executable, *flags, *common]
    result = subprocess.run(
        command, cwd=package, env=env, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    raw = result.stdout
    target = packet / "raw" / f"adapter-suite-{name}.stdout.txt"
    Path(str(target) + ".b64").write_bytes(base64.b64encode(raw) + b"\n")
    rows.append((name, result.returncode, hashlib.sha256(raw).hexdigest(),
                 len(raw), command))
    if result.returncode:
        sys.stdout.buffer.write(raw)
        raise SystemExit(result.returncode)

status = [f"Python: {sys.version}", f"Platform: {sys.platform}"]
status.extend(
    f"{name}: exit={code}; sha256={digest}; bytes={size}; command={' '.join(command)}"
    for name, code, digest, size, command in rows
)
status_raw = ("\n".join(status) + "\n").encode("utf-8")
status_path = packet / "raw" / "adapter-suite-status.txt"
Path(str(status_path) + ".b64").write_bytes(base64.b64encode(status_raw) + b"\n")
sums = [f"{digest}  raw/adapter-suite-{name}.stdout.txt"
        for name, _, digest, _, _ in rows]
sums.append(f"{hashlib.sha256(status_raw).hexdigest()}  raw/adapter-suite-status.txt")
(packet / "SHA256SUMS").write_text("\n".join(sums) + "\n", encoding="ascii")
print("\n".join(status))
