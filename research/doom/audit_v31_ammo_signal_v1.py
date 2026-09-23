"""Model-free audit of exact ammo extraction over the retained v31 run."""
import argparse
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ROOT = HERE / "results/map01-soft-context-v31-live-01"
WAD = REPO / "_vizdoom/vizdoom/freedoom2.wad"
sys.path.insert(0, str(HERE))
from doom_hud_signal_v2 import DoomStatusNumberReader


def run():
    report = json.loads((ROOT / "report.json").read_text())
    events = [json.loads(line) for line in
              (ROOT / "runtime/events.jsonl").read_text().splitlines()]
    observations = [row for row in events if row.get("event") == "observation"]
    reader = DoomStatusNumberReader(
        WAD, signal_id="ammo",
        image_resolver=lambda value: ROOT / "runtime" / Path(value).name)
    signals = [reader.read(row) for row in observations]
    assert len(signals) == 247 and all(row["status"] == "observed" for row in signals)
    transitions = []
    for signal in signals:
        pair = [signal["sequence"], signal["value"]]
        if not transitions or pair[1] != transitions[-1][1]:
            transitions.append(pair)
    review = json.loads((ROOT / "analysis/threat-review.json").read_text())
    decision_sequences = [decision["cover_validity_admission"]["source_signal"]["sequence"]
                          for decision in report["decisions"]]
    by_sequence = {row["sequence"]: row["value"] for row in signals}
    decision_ammo = [by_sequence[sequence] for sequence in decision_sequences]
    manual_ammo = [row["ammo"] for row in review["decisions"]]
    assert decision_ammo == manual_ammo == [48, 48, 47, 47, 46, 45, 45, 45]
    return {
        "schema": "retained-v31-ammo-signal-audit-v1",
        "passed": True,
        "exact_ammo_signals": len(signals),
        "unknown_ammo_signals": 0,
        "ammo_transitions": transitions,
        "decision_sequences": decision_sequences,
        "decision_ammo": decision_ammo,
        "independent_manual_ammo": manual_ammo,
        "model_calls": 0,
        "input_operations": 0,
        "finding": "the adjacent WAD-glyph HUD reader extracts ammo from every retained exact frame and matches all independently transcribed decision frames",
        "limits": "retained-trace signal construction only; ammunition availability cannot establish target presence, aim, action usefulness, live latency, gameplay gain, or generality",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = run()
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "audit.json").write_bytes(
        (json.dumps(result, indent=2) + "\n").encode("utf-8"))
    print(json.dumps(result, separators=(",", ":")))


if __name__ == "__main__":
    main()
