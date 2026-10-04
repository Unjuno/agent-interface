import hashlib
import json
import subprocess
import sys
from pathlib import Path


out = Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)
command = ["wslc.exe", "ps", "--all", "--format", "json"]
result = subprocess.run(command, stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE, check=False)
(out / "preflight-list.stdout.bin").write_bytes(result.stdout)
(out / "preflight-list.stderr.bin").write_bytes(result.stderr)
(out / "preflight-list.exit-code.txt").write_text(
    str(result.returncode) + "\n", encoding="ascii")
receipt = {
    "command": command,
    "exit_code": result.returncode,
    "stdout_bytes": len(result.stdout),
    "stderr_bytes": len(result.stderr),
    "stdout_sha256": hashlib.sha256(result.stdout).hexdigest(),
    "stderr_sha256": hashlib.sha256(result.stderr).hexdigest(),
    "stdout_interpretation": ("empty-byte-output" if not result.stdout
                              else "raw-json-or-text-retained"),
}
entries = []
parse_errors = []
for line_number, line in enumerate(result.stdout.decode("utf-8", "replace").splitlines(), 1):
    if not line.strip():
        continue
    try:
        item = json.loads(line)
        if type(item) is not dict or type(item.get("State")) is not str:
            raise ValueError("row is not an object with a string State")
        entries.append(item)
    except (json.JSONDecodeError, ValueError) as exc:
        parse_errors.append({"line": line_number, "error": str(exc)})
nonterminal = [
    {"id": item.get("ID"), "name": item.get("Names"), "state": item.get("State")}
    for item in entries if item["State"].lower() not in {"exited", "dead"}
]
receipt.update({
    "rows_parsed": len(entries),
    "parse_errors": parse_errors,
    "nonterminal_rows": nonterminal,
    "start_gate": ("CLEAR" if result.returncode == 0 and not parse_errors and
                   not nonterminal else "HOLD"),
})
(out / "preflight-list.capture.json").write_text(
    json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
print(json.dumps(receipt, indent=2))
