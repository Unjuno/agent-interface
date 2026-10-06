"""Probe strict frame-specific transforms against the OpenTTD resolutions."""
import json

from coordinate_frame_transform_v1 import transform, translation


SOURCE = [129, 40, 1024, 720]
TARGET_1280 = [1, 40, 1280, 720]
TARGET_1152 = [65, 40, 1152, 720]
FIRST = [{"x": 705, "y": 239}, {"x": 673, "y": 255}, {"x": 641, "y": 271}]


def refuses(call):
    try:
        call()
    except ValueError as error:
        return str(error)
    raise AssertionError("invalid transform was accepted")


def main():
    chrome_1280 = transform("screen_chrome", SOURCE, TARGET_1280, [{"x": 820, "y": 51}])
    content_1280 = transform("window_content", SOURCE, TARGET_1280, FIRST)
    content_1152 = transform("window_content", SOURCE, TARGET_1152, FIRST)
    assert chrome_1280["points"] == [{"x": 820, "y": 51}]
    assert content_1280["translation"] == [-128, 0]
    assert content_1280["points"][0] == {"x": 577, "y": 239}
    assert content_1152["translation"] == [-64, 0]
    assert content_1152["points"][0] == {"x": 641, "y": 239}
    report = {"probe_passed": True,
        "source_geometry": SOURCE,
        "screen_chrome_1280": chrome_1280,
        "window_content_1280": content_1280,
        "window_content_1152": content_1152,
        "refusals": {
            "unknown_frame": refuses(lambda: translation("map", SOURCE, TARGET_1280)),
            "bad_geometry": refuses(lambda: translation("window_content", [0, 0, 0, 1], TARGET_1280)),
            "bad_delta": refuses(lambda: transform("window_content", SOURCE, TARGET_1280,
                                                    [{"x": 1, "y": 2, "z": 3}])),
        },
        "scope": "pure explicit-frame translation; no automatic frame classification, application input or broad layout claim"}
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
