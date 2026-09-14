"""Regression for v2 low-information mint refusal."""
from PIL import Image

from scoped_target_handle_v2 import TargetHandleStore


def observation():
    return {"sequence": 1, "capture_ns": 1_000_000_000,
            "pointer_binding": {"focus": 20, "surface": 30,
                                "geometry": [10, 10, 100, 70]}}


def main():
    store = TargetHandleStore("fixture", lambda: "textured")
    flat = Image.new("RGB", (120, 90), (9, 9, 9))
    try:
        store.mint("flat", "window_content", [20, 20, 8, 8], observation(),
                   flat, 1_000_000_100)
    except ValueError as error:
        assert str(error) == "visually flat target region refused"
    else:
        raise AssertionError("flat handle source accepted")
    textured = flat.copy()
    for x in range(8):
        for y in range(8):
            textured.putpixel((20 + x, 20 + y), (x * 29, y * 31, (x + y) * 13))
    minted = store.mint("textured", "window_content", [20, 20, 8, 8],
                        observation(), textured, 1_000_000_100)
    assert minted["status"] == "VALID" and minted["handle"] == "textured"
    print("scoped_target_handle_v2_probe_passed")


if __name__ == "__main__":
    main()
