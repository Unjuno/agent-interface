"""Probe position-independent OpenTTD toolbar discovery on archived pixels."""
import json
import time
from pathlib import Path

from PIL import Image

from openttd_toolbar_slots_v2 import discover


HERE = Path(__file__).resolve().parent
SOURCE = (HERE / "results/openttd-active-evidence-pair-02/2-stable-seed991004/"
          "runtime/010.png")


def translated(image, dx, dy):
    output = Image.new("RGB", image.size, "black")
    output.paste(image, (dx, dy))
    return output


def main():
    with Image.open(SOURCE) as opened:
        source = opened.convert("RGB")
    started = time.perf_counter_ns()
    baseline = discover(source)
    baseline_ms = (time.perf_counter_ns() - started) / 1e6
    assert baseline["row"] == 40 and len(baseline["slots"]) == 30
    cases = []
    for dx, dy in ((21, 28), (-17, 11), (7, -19)):
        result = discover(translated(source, dx, dy))
        assert result["row"] == baseline["row"] + dy
        assert len(result["slots"]) == 30
        for original, shifted in zip(baseline["slots"], result["slots"]):
            assert shifted["point"] == [original["point"][0] + dx,
                                        original["point"][1] + dy]
        cases.append({"delta": [dx, dy], "row": result["row"],
                      "first": result["slots"][0]["point"],
                      "last": result["slots"][-1]["point"]})
    try:
        discover(Image.new("RGB", source.size, "black"))
    except ValueError as error:
        assert str(error) == "repeated toolbar slot row missing"
    else:
        raise AssertionError("missing toolbar was accepted")
    assert baseline_ms < 1000
    print(json.dumps({"baseline_row": baseline["row"], "slots": 30,
                      "baseline_ms": baseline_ms,
                      "translations": cases, "missing_refused": True}))


if __name__ == "__main__":
    main()
