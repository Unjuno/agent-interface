"""Probe translated finance scoring and stale/wrong-delta controls."""
import json
from pathlib import Path

from PIL import Image

from openttd_finance_oracle_v2 import score


HERE = Path(__file__).resolve().parent
ROOT = HERE / "results/openttd-active-evidence-pair-02/2-stable-seed991004"


def main():
    result = json.loads((ROOT / "result.json").read_text(encoding="utf-8"))
    source = ROOT / "runtime" / Path(result["final_observation"]["image"]).name
    with Image.open(source) as opened:
        original = opened.convert("RGB")
    delta = [21, 28]
    translated = Image.new("RGB", original.size, "black")
    translated.paste(original, tuple(delta))
    assert score(translated, delta)["success"] is True
    assert score(translated, [0, 0])["success"] is False
    assert score(translated, [20, 28])["success"] is False
    try:
        score(translated, [2000, 0])
    except ValueError as error:
        assert str(error) == "translated finance-title region outside image"
    else:
        raise AssertionError("out-of-bounds translated oracle was accepted")
    print(json.dumps({"translated_success": True, "stale_refused": True,
                      "wrong_delta_false": True, "bounds_refused": True}))


if __name__ == "__main__":
    main()
