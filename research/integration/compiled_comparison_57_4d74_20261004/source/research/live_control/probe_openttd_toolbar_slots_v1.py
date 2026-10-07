"""Deterministic checks for meaning-free toolbar slot discovery and expansion."""
from pathlib import Path

from openttd_toolbar_slots_v1 import discover, expand, local_neighbourhood


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "results/openttd-active-evidence-pair-01/2-stable-seed991004/runtime/014.png"


def refused(function, *args, **kwargs):
    try:
        function(*args, **kwargs)
    except ValueError:
        return True
    raise AssertionError("invalid toolbar discovery input was accepted")


def main():
    slots = discover(SOURCE)
    assert len(slots) == 30
    assert slots[0]["point"] == [294, 51]
    assert slots[-1]["point"] == [984, 51]
    expanded = expand([[436, 51], [412, 51], [460, 51]], slots)
    assert expanded["points"] == [
        [389, 51], [412, 51], [435, 51], [458, 51], [485, 51]]
    assert expanded["authority"].endswith("grants no input authority")
    local = local_neighbourhood([433, 51], slots)
    assert local["points"] == [
        [389, 51], [412, 51], [435, 51], [458, 51], [485, 51]]
    invalid = [
        refused(discover, SOURCE, row=-1),
        refused(expand, [], slots),
        refused(expand, [[1.5, 2]], slots),
        refused(expand, [[294, 51], [961, 51]], slots),
        refused(local_neighbourhood, [1.5, 2], slots),
    ]
    assert all(invalid)
    print({"slots": len(slots), "expanded_points": expanded["points"],
           "local_points": local["points"],
           "invalid_inputs_refused": len(invalid)})


if __name__ == "__main__":
    main()
