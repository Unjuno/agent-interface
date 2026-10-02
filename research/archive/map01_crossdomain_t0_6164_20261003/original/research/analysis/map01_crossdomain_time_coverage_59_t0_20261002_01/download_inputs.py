"""Fetch only the six frozen, public source files and verify SHA-256."""
import hashlib
from pathlib import Path
from urllib.request import urlopen

COMMIT = "279ee4aee96c5646360239409931821726566aa2"
INPUTS = {
    "doom-v38-events.jsonl": (
        "research/doom/results/map01-v38-integrated-threat-live-01/runtime/events.jsonl",
        "80b964c9ab7d86fbd0b2bc56957157e018e9dbb90457f286995a2e6036192bc3"),
    "doom-v39-events.jsonl": (
        "research/doom/results/map01-v39-coast-liveness-live-01/runtime/events.jsonl",
        "2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381"),
    "doom-analysis.json": (
        "research/doom/results/map01-v38-v39-control-tempo-posthoc-v1/analysis.json",
        "7b7541174c39fac708ba6c28f371f40fb68bf71743e66c9fbcb517d45e78bf71"),
    "openttd-events.jsonl": (
        "research/live_control/results/timing-envelope-openttd-l-06/fixed-astra/runtime/events.jsonl",
        "b9e707b006a918b232f6d8915adc6a95e4d7e4ee789fec7ef4e1fba7e2df61ae"),
    "openttd-observer.txt": (
        "research/live_control/results/timing-envelope-openttd-l-06/fixed-astra/runtime/game-stderr.txt",
        "4bcfb5b2632e9b2dc76f5e3f67a73f30cbd6b142578b495f0b204a2ec9696ca4"),
    "openttd-audit.json": (
        "research/live_control/results/timing-envelope-openttd-l-06/posthoc-audit.json",
        "8377e663d6f3b88eb41b73d85212f903f21b4879010835f9e2d1f100de4bee5c"),
}


def main():
    root = Path(__file__).resolve().parent / "inputs"
    root.mkdir(exist_ok=True)
    for name, (path, expected) in INPUTS.items():
        url = f"https://raw.githubusercontent.com/Unjuno/agent-interface/{COMMIT}/{path}"
        with urlopen(url, timeout=30) as response:
            data = response.read()
        observed = hashlib.sha256(data).hexdigest()
        if observed != expected:
            raise SystemExit(f"STOP_INPUT_HASH_MISMATCH:{name}:{observed}")
        (root / name).write_bytes(data)
        print(f"PASS_INPUT:{name}:{observed}")


if __name__ == "__main__":
    main()
