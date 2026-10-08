import json
from pathlib import Path


ROOT = Path(__file__).parent


def load_inputs():
    protocol = json.loads((ROOT / "protocol.json").read_text())
    fixture = json.loads((ROOT / "fixture.json").read_text())
    truth = json.loads((ROOT / "truth.json").read_text())
    return protocol, fixture, truth
