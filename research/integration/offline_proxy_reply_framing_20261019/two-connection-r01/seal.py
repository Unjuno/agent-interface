"""Compress captured test outputs and seal source/results without rerunning."""

import gzip
import hashlib
import json
import platform
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]
RUNS = {
    "protocol-and-relay-normal": ("protocol-and-relay-normal.raw.txt", 28),
    "protocol-and-relay-optimized": ("protocol-and-relay-optimized.raw.txt", 28),
    "standard-caller-composition-normal": ("standard-caller-composition-normal.raw.txt", 3),
    "standard-caller-composition-optimized": ("standard-caller-composition-optimized.raw.txt", 3),
}
receipt = {"python": platform.python_version(), "platform": platform.platform(), "runs": {}}
for label, (raw_name, expected_count) in RUNS.items():
    raw_path = ROOT / raw_name
    compressed_name = label + ".raw.gz"
    compressed_path = ROOT / compressed_name
    if raw_path.exists():
        data = raw_path.read_bytes()
    else:
        data = gzip.decompress(compressed_path.read_bytes())
    text = data.decode("utf-8", errors="replace")
    match = re.search(r"Ran (\d+) tests? in ", text)
    if not match or int(match.group(1)) != expected_count or not text.rstrip().endswith("OK"):
        raise SystemExit(f"{label}: output is not a passing {expected_count}-test receipt")
    if raw_path.exists():
        compressed = gzip.compress(data, mtime=0)
        compressed_path.write_bytes(compressed)
        raw_path.unlink()
    else:
        compressed = compressed_path.read_bytes()
    receipt["runs"][label] = {"test_count": expected_count, "status": "PASS",
        "raw_file": compressed_name, "raw_sha256": hashlib.sha256(data).hexdigest(),
        "compressed_sha256": hashlib.sha256(compressed).hexdigest()}
(ROOT / "receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True)+"\n",
                                    encoding="utf-8", newline="\n")
sources = [
    "research/integration/offline_proxy_reply_framing_20261019/proxy_candidate.py",
    "research/integration/offline_proxy_reply_framing_20261019/fake_socket_relay.py",
    "research/integration/offline_proxy_reply_framing_20261019/test_reply_gate.py",
    "research/integration/offline_proxy_reply_framing_20261019/test_proxy_candidate.py",
    "research/integration/offline_proxy_reply_framing_20261019/test_fake_socket_relay.py",
    "research/integration/offline_proxy_reply_framing_20261019/test_two_connection_relay.py",
    "runtime/cli_v1/test_mcp_relay_composition.py",
]
own_names = ["README.md", "conditions.json", "seal.py", "receipt.json"]
own_names.extend(label + ".raw.gz" for label in RUNS)
own_names.extend(["runner-import-failure.json", "runner-import-failure.raw.gz",
                  "runner-import-failure-2.json", "runner-import-failure-2.raw.gz"])
own = ["research/integration/offline_proxy_reply_framing_20261019/two-connection-r01/"+name
       for name in own_names]
lines = [f"{hashlib.sha256((REPO / name).read_bytes()).hexdigest()}  {name}"
         for name in sources + own]
(ROOT / "SHA256SUMS").write_text("\n".join(lines)+"\n", encoding="ascii", newline="\n")
print(json.dumps(receipt, indent=2, sort_keys=True))
print(f"sealed {len(lines)} source and result files")
