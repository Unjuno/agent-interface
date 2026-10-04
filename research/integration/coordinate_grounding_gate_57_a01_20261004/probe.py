"""Model-free coordinate-to-handle composition probe against current runtime APIs."""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw

from runtime.guarded_x11_v1.handles import TargetHandleStore
from runtime.guarded_x11_v1.handles_texture import FlatTargetRefused


WIDTH, HEIGHT = 180, 100
REGION = 24
MODEL_POINT = [80, 48]
SOURCE_CAPTURE_NS = 1_000_000
NOW_NS = 2_000_000


def observation(sequence, capture_ns, *, focus=101, surface=202, geometry=None):
    return {
        "sequence": sequence,
        "capture_ns": capture_ns,
        "pointer_binding": {
            "focus": focus,
            "surface": surface,
            "geometry": list(geometry or [0, 0, WIDTH, HEIGHT]),
        },
    }


def image_with_target(point=MODEL_POINT, *, flat=False):
    image = Image.new("RGB", (WIDTH, HEIGHT), (18, 24, 31))
    x0, y0 = point[0] - REGION // 2, point[1] - REGION // 2
    draw = ImageDraw.Draw(image)
    if flat:
        draw.rectangle((x0, y0, x0 + REGION - 1, y0 + REGION - 1), fill=(120, 120, 120))
    else:
        for y in range(REGION):
            for x in range(REGION):
                color = ((x * 37 + y * 11) % 256,
                         (x * 13 + y * 43 + 7) % 256,
                         (x * 29 + y * 19 + 53) % 256)
                image.putpixel((x0 + x, y0 + y), color)
    return image


def mint_model_coordinate(store, point, source_observation, source_image, *, alias="model_target",
                          search_radius=1):
    """Interpret the model point only as a source-region proposal, never authority."""
    if (type(point) is not list or len(point) != 2 or
            any(type(value) is not int for value in point)):
        raise ValueError("model coordinate must be two exact integers")
    box = [point[0] - REGION // 2, point[1] - REGION // 2, REGION, REGION]
    return store.mint(
        alias, "window_content", box, source_observation, source_image,
        NOW_NS, ttl_ms=300_000, freshness_ms=1_500, search_radius=search_radius,
        allowed_transformations=("window_translation",),
    )


def new_store():
    return TargetHandleStore("coordinate-grounding-a01", id_factory=lambda: "private-id")


def run_probe():
    source_image = image_with_target()
    source_obs = observation(1, SOURCE_CAPTURE_NS)
    outcomes = {}

    store = new_store()
    minted = mint_model_coordinate(store, list(MODEL_POINT), source_obs, source_image)
    fresh_obs = observation(2, NOW_NS)
    outcomes["unchanged_fresh"] = store.resolve_point(
        minted["handle"], [REGION // 2, REGION // 2], fresh_obs,
        source_image.copy(), NOW_NS + 1_000_000,
    )

    store = new_store()
    minted = mint_model_coordinate(store, list(MODEL_POINT), source_obs, source_image)
    changed_image = source_image.copy()
    draw = ImageDraw.Draw(changed_image)
    x0, y0 = MODEL_POINT[0] - REGION // 2, MODEL_POINT[1] - REGION // 2
    draw.rectangle((x0, y0, x0 + REGION - 1, y0 + REGION - 1), fill=(2, 3, 4))
    outcomes["changed_target"] = store.resolve_point(
        minted["handle"], [REGION // 2, REGION // 2], fresh_obs,
        changed_image, NOW_NS + 1_000_000,
    )

    store = new_store()
    minted = mint_model_coordinate(store, list(MODEL_POINT), source_obs, source_image,
                                   search_radius=64)
    duplicate_image = source_image.copy()
    x0, y0 = MODEL_POINT[0] - REGION // 2, MODEL_POINT[1] - REGION // 2
    duplicate_image.paste(source_image.crop((x0, y0, x0 + REGION, y0 + REGION)), (130, 10))
    outcomes["duplicate_target"] = store.resolve_point(
        minted["handle"], [REGION // 2, REGION // 2], fresh_obs,
        duplicate_image, NOW_NS + 1_000_000,
    )

    store = new_store()
    minted = mint_model_coordinate(store, list(MODEL_POINT), source_obs, source_image)
    outcomes["focus_changed"] = store.resolve_point(
        minted["handle"], [REGION // 2, REGION // 2],
        observation(2, NOW_NS, focus=303), source_image.copy(), NOW_NS + 1_000_000,
    )

    store = new_store()
    minted = mint_model_coordinate(store, list(MODEL_POINT), source_obs, source_image)
    outcomes["window_translation"] = store.resolve_point(
        minted["handle"], [REGION // 2, REGION // 2],
        observation(2, NOW_NS, geometry=[5, 0, WIDTH, HEIGHT]),
        image_with_target([MODEL_POINT[0] + 5, MODEL_POINT[1]]), NOW_NS + 1_000_000,
    )

    store = new_store()
    minted = mint_model_coordinate(store, list(MODEL_POINT), source_obs, source_image)
    outcomes["local_move"] = store.resolve_point(
        minted["handle"], [REGION // 2, REGION // 2], fresh_obs,
        image_with_target([MODEL_POINT[0] + 1, MODEL_POINT[1]]), NOW_NS + 1_000_000,
    )

    store = new_store()
    minted = mint_model_coordinate(store, list(MODEL_POINT), source_obs, source_image)
    outcomes["stale_observation"] = store.resolve_point(
        minted["handle"], [REGION // 2, REGION // 2],
        observation(2, 0), source_image.copy(), 1_600_000_000,
    )

    store = new_store()
    missing_alias = store.resolve_point(
        "not_minted", [REGION // 2, REGION // 2], fresh_obs,
        source_image.copy(), NOW_NS + 1_000_000,
    )
    outcomes["missing_alias"] = missing_alias

    flat_store = new_store()
    flat_refused = False
    try:
        mint_model_coordinate(flat_store, list(MODEL_POINT), source_obs,
                              image_with_target(flat=True))
    except FlatTargetRefused:
        flat_refused = True

    boundary_refused = False
    try:
        mint_model_coordinate(new_store(), [5, 5], source_obs, source_image,
                              alias="out_of_bounds")
    except ValueError:
        boundary_refused = True

    serialized = {
        name: {
            "status": value["status"],
            "eligible": value["eligible"],
            "authority": value["authority"],
            "reason": value.get("reason"),
            "point": value.get("point"),
        }
        for name, value in outcomes.items()
    }
    return {
        "schema": "coordinate-grounding-a01-result-v1",
        "source_sequence": 1,
        "fresh_sequence": 2,
        "model_coordinate": MODEL_POINT,
        "case_results": serialized,
        "flat_source_refused_before_registry_insert": flat_refused and not flat_store._entries,
        "out_of_bounds_refused": boundary_refused,
        "input_dispatch_count": 0,
        "claim_scope": "synthetic image + current target-handle APIs; no model, GUI, or input dispatch",
    }


if __name__ == "__main__":
    print(json.dumps(run_probe(), indent=2, sort_keys=True))
