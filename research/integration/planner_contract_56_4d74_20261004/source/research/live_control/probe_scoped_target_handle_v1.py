"""Deterministic controls for scoped exact-region target handles."""
import copy
import json

from PIL import Image

from scoped_target_handle_v1 import TargetHandleStore


def observation(sequence=1, capture_ns=1_000_000_000, focus=20, surface=30,
                geometry=None):
    return {"sequence": sequence, "capture_ns": capture_ns,
            "pointer_binding": {"focus": focus, "surface": surface,
                                "geometry": list(geometry or [10, 10, 100, 70])}}


def canvas(locations):
    image = Image.new("RGB", (140, 100), (8, 12, 16))
    patch = Image.new("RGB", (8, 8))
    pixels = patch.load()
    for y in range(8):
        for x in range(8):
            pixels[x, y] = ((x * 31 + y * 7) % 256,
                            (x * 11 + y * 29) % 256, (x * 17 + y * 13) % 256)
    for location in locations:
        image.paste(patch, location)
    return image


def main():
    ids = iter(("window-only", "locally-mobile"))
    store = TargetHandleStore("fixture-session", lambda: next(ids))
    source = observation()
    first = store.mint("primary_action", "window_content", [40, 30, 8, 8],
                       source, canvas([(40, 30)]), 1_000_000_100,
                       ttl_ms=1000, freshness_ms=100, search_radius=12)
    second = store.mint("movable_action", "window_content", [40, 30, 8, 8],
                        source, canvas([(40, 30)]), 1_000_000_100,
                        ttl_ms=1000, freshness_ms=100, search_radius=12,
                        allowed_transformations=("window_translation", "local_translation"))
    stable = store.resolve_point(first["handle"], [3, 4], observation(2),
                                 canvas([(40, 30)]), 1_000_000_200)
    moved_window = store.resolve_point(
        first["handle"], [3, 4], observation(2, geometry=[15, 13, 100, 70]),
        canvas([(45, 33)]), 1_000_000_200)
    local_refused = store.resolve_point(first["handle"], [3, 4], observation(2),
                                        canvas([(46, 30)]), 1_000_000_200)
    local_allowed = store.resolve_point(second["handle"], [3, 4], observation(2),
                                        canvas([(46, 30)]), 1_000_000_200)
    duplicated = store.resolve_point(second["handle"], [3, 4], observation(2),
                                     canvas([(38, 30), (46, 30)]), 1_000_000_200)
    missing = store.resolve_point(first["handle"], [3, 4], observation(2),
                                  canvas([]), 1_000_000_200)
    stale = store.resolve_point(first["handle"], [3, 4],
                                observation(2, capture_ns=2_100_000_000),
                                canvas([(40, 30)]), 2_100_000_001)
    wrong_session = store.resolve_point(first["handle"], [3, 4], observation(2),
                                        canvas([(40, 30)]), 1_000_000_200,
                                        session_scope="other-session")
    changed_surface_observation = copy.deepcopy(observation(2))
    changed_surface_observation["pointer_binding"]["surface"] = 31
    wrong_surface = store.resolve_point(first["handle"], [3, 4],
                                        changed_surface_observation,
                                        canvas([(40, 30)]), 1_000_000_200)
    unknown = store.resolve_point("absent", [3, 4], observation(2),
                                  canvas([(40, 30)]), 1_000_000_200)
    outcomes = {"stable": stable, "window_translation": moved_window,
                "local_refused": local_refused, "local_allowed": local_allowed,
                "ambiguous": duplicated, "missing": missing, "stale": stale,
                "wrong_session": wrong_session, "wrong_surface": wrong_surface,
                "unknown": unknown}
    expected = {"stable": "VALID", "window_translation": "REVALIDATED",
                "local_refused": "MOVED", "local_allowed": "REVALIDATED",
                "ambiguous": "AMBIGUOUS", "missing": "MISSING", "stale": "STALE",
                "wrong_session": "SCOPE_MISMATCH", "wrong_surface": "SCOPE_MISMATCH",
                "unknown": "MISSING"}
    assert {name: result["status"] for name, result in outcomes.items()} == expected
    assert stable["point"] == [43, 34]
    assert moved_window["point"] == [48, 37]
    assert local_allowed["point"] == [49, 34]
    assert all(result["eligible"] == (expected[name] in ("VALID", "REVALIDATED"))
               for name, result in outcomes.items())
    assert all(result["authority"].startswith("resolution only")
               for result in outcomes.values())
    print(json.dumps({"passed": True, "statuses": expected,
                      "resolved_points": {"stable": stable["point"],
                                          "window_translation": moved_window["point"],
                                          "local_allowed": local_allowed["point"]},
                      "scope": "synthetic deterministic contract controls; no GUI input"},
                     indent=2))


if __name__ == "__main__":
    main()
