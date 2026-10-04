"""Independently verify the retained marker lifecycle probe receipt."""
import hashlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXPECTED = {
    "input_transition_owner_v3.py":
        "672e7471b91f321f0d8723ef6277d974b24b2fa322f5e89907b17bf92998f177",
    "input_owner_v10.py":
        "ceae7d9983cd0ba13a35e01ce2ce7dbbf03a0397b23ddc123b0110b4d4de670b",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


repo = HERE.parents[2]
for name, expected in EXPECTED.items():
    path = repo / "research/live_control" / name
    if digest(path) != expected:
        raise SystemExit(f"FAIL source hash mismatch: {name}")
    print(f"PASS source hash: {name}")

raw = (HERE / "results/RAW_PROBE.txt").read_text(encoding="utf-8")
exit_code = (HERE / "results/EXIT_CODE.txt").read_text(encoding="utf-8").strip()
expected_line = ("PASS cycles=64 verified_cancel_cleanup=64 key_events=128 "
                 "peak_markers=1 final_markers=1")
if exit_code != "0" or raw.strip() != expected_line:
    raise SystemExit("FAIL retained probe receipt")
print("PASS raw output and exit receipt")
