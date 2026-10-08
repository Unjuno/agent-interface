"""Independent parser for the retained WSLc memory-cap receipt; never imports probe.py."""
from __future__ import annotations
import hashlib
import json
import re
import sys
from pathlib import Path

EXPECTED = {
    "probe.py": "FCC6AF165725F7654EB15541A8F9014B233308DB595D897325B1B758345B1D47",
    "commands.txt": "F848BB09859D99811E53E27FE06D845B8F5122C062F35D32BE8D1E6105B8A7B4",
    "raw.log": "69C1AA9B29DD45397376A1820333DB2FA8F23A6AC5C9FF1769802ABD14FF17AE",
    "REPORT.md": "4974DC244F3D93FEA173DA121F49D4A2AAAD407C882798B8058CC9F7F1410BE9",
}
WARNING = "wsl: Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap."
IMAGE = "python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f"

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()

def audit(root: Path) -> dict:
    files = {name: (root / name).read_bytes() for name in EXPECTED}
    manifest = (root / "SHA256SUMS.txt").read_text(encoding="utf-8")
    listed = {}
    for line in manifest.splitlines():
        m = re.fullmatch(r"([0-9A-F]{64})  ([A-Za-z0-9_.-]+)", line)
        if not m or m.group(2) in listed:
            raise ValueError("malformed or duplicate manifest entry")
        listed[m.group(2)] = m.group(1)
    if listed != EXPECTED:
        raise ValueError("manifest entries differ from frozen expected names/digests")
    observed = {name: sha(data) for name, data in files.items()}
    if observed != EXPECTED:
        raise ValueError("retained input digest mismatch")
    if sha(files["probe.py"]) != EXPECTED["probe.py"]:
        raise ValueError("probe source digest mismatch")

    commands = files["commands.txt"].decode("utf-8").splitlines()
    command_rows = [line for line in commands if line.startswith("wslc run ")]
    if len(command_rows) != 2:
        raise ValueError("expected exactly two frozen WSLc command rows")
    normalized = []
    limits = []
    for line in command_rows:
        matches = re.findall(r"--memory ([0-9]+M)", line)
        if len(matches) != 1:
            raise ValueError("each command must specify exactly one memory request")
        limits.append(matches[0])
        for required in ("--rm", "--pull never", "--network none", "--cpus 1",
                         IMAGE, "python /probe.py 384"):
            if required not in line:
                raise ValueError("frozen command lacks required argument: " + required)
        mount = re.search(r"--mount 'type=bind,source=([^']+),target=/probe\.py,readonly'", line)
        if not mount or not mount.group(1).endswith("\\probe.py"):
            raise ValueError("command does not bind one absolute Windows probe.py read-only")
        normalized.append(re.sub(r"--memory [0-9]+M", "--memory <LIMIT>", line))
    if limits != ["512M", "128M"] or normalized[0] != normalized[1]:
        raise ValueError("commands are not an otherwise-matched 512M/128M pair")

    raw = files["raw.log"].decode("utf-8")
    for token in (
        "WSL package: 3.0.1.0", "WSLc: 3.0.1",
        "Image: " + IMAGE, "Source SHA256: " + EXPECTED["probe.py"],
    ):
        if token not in raw:
            raise ValueError("raw log missing frozen identity: " + token)
    if raw.count(WARNING) != 2:
        raise ValueError("expected the cgroup/swap warning in both arms")
    sections = re.findall(r"\[(512M control|128M constrained)\]\n(.*?)(?=\n\[|\Z)", raw, re.S)
    if [label for label, _ in sections] != ["512M control", "128M constrained"]:
        raise ValueError("expected exactly ordered control and constrained sections")
    observed_arms = []
    expected_max = {"512M control": "536870912", "128M constrained": "134217728"}
    for label, body in sections:
        arm_index = len(observed_arms)
        expected_lines = [
            "$ " + command_rows[arm_index], WARNING, "cgroup 0::/",
            "memory.max " + expected_max[label], "ALLOCATED_MIB=384",
            "exit code: 0",
        ]
        for item in expected_lines:
            if body.count(item) != 1:
                raise ValueError(f"{label}: expected exactly one {item!r}")
        observed_arms.append({
            "arm": label, "memory_max_bytes": int(expected_max[label]),
            "allocated_mib": 384, "exit_code": 0, "warning_present": True,
        })
    report = files["REPORT.md"].decode("utf-8")
    if "**D:** **FAIL (scoped)**" not in report or "both arms emitted" not in report:
        raise ValueError("report does not retain the scoped failed hypothesis")
    return {
        "status": "PASS_INDEPENDENT_AUDIT_SCOPED",
        "source_sha256": sha(files["probe.py"]),
        "input_sha256": observed,
        "commands": {"memory_limits": limits, "otherwise_identical": True},
        "arms": observed_arms,
        "interpretation": "requested memory.max values were reported but both runs retained 384 MiB and exited 0; effective enforcement not demonstrated",
        "limits": ["stdout/stderr merged in predecessor raw", "no kernel-level or peak-RSS proof", "no Docker comparison", "no representative workload"],
    }

if __name__ == "__main__":
    try:
        result = audit(Path(sys.argv[1]))
        encoded = json.dumps(result, sort_keys=True, separators=(",", ":"))
        if len(sys.argv) > 2:
            Path(sys.argv[2]).write_text(encoded + "\n", encoding="utf-8", newline="\n")
        print(encoded)
    except Exception as exc:
        encoded = json.dumps({"status": "FAIL_AUDIT", "error": type(exc).__name__ + ": " + str(exc)}, sort_keys=True, separators=(",", ":"))
        if len(sys.argv) > 2:
            Path(sys.argv[2]).write_text(encoded + "\n", encoding="utf-8", newline="\n")
        print(encoded)
        raise SystemExit(1)
