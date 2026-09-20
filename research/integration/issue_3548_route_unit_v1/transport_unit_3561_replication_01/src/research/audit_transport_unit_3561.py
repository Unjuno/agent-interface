#!/usr/bin/env python3
"""Independent raw audit; does not import the API, CLI, runner, or MCP code."""
import hashlib
import json
from pathlib import Path
import sys

from PIL import Image

EXPECTED_ROUTES = ("api", "cli", "mcp")
EXPECTED_REGION = [0, 0, 500, 260]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def nested_observation(route_row):
    if route_row["route"] in ("api", "cli"):
        return route_row["raw_result"].get("observation", {})
    metadata = route_row["raw_result"].get("metadata", {})
    receipt = metadata.get("receipt", {})
    raw = receipt.get("source", {}).get("raw_report", {})
    return raw.get("observation", {})


def audit(evidence_dir):
    root = Path(evidence_dir)
    summary = json.loads((root/"summary.json").read_text())
    if summary.get("route_count") != 3 or tuple(summary.get("routes", [])) != EXPECTED_ROUTES:
        raise ValueError("route denominator or order mismatch")
    if summary.get("network") != "none" or summary.get("input_dispatched") is not False:
        raise ValueError("network/input boundary mismatch")
    if summary.get("failure") is not None:
        raise ValueError("runner retained a route failure")
    if summary.get("xvfb_cleanup", {}).get("reaped") is not True:
        raise ValueError("Xvfb not reaped")
    if summary.get("xvfb_cleanup", {}).get("exit_code") != -15:
        raise ValueError("Xvfb did not terminate by recorded harness signal")

    pixels = {}
    png_hashes = {}
    raw_hashes = {}
    for route in EXPECTED_ROUTES:
        row = json.loads((root/f"{route}.json").read_text())
        attempt = json.loads((root/f"{route}-attempt.json").read_text())
        if row.get("route") != route or attempt.get("route") != route:
            raise ValueError("route label mismatch")
        if attempt.get("attempt_count") != 1 or attempt.get("observation_count") != 1:
            raise ValueError("route call count mismatch")
        if attempt.get("fixture_cleanup", {}).get("reaped") is not True:
            raise ValueError("fixture process not reaped: "+route)
        if attempt.get("fixture_cleanup", {}).get("exit_code") != -15:
            raise ValueError("fixture process exit mismatch: "+route)
        if row.get("status") != "returned" or row.get("return_code") != 0:
            raise ValueError("route did not return successfully: "+route)
        if row.get("input_dispatched") is not False:
            raise ValueError("input was not explicitly absent: "+route)
        if row.get("elapsed_ns", 0) <= 0:
            raise ValueError("invalid route clock: "+route)
        req = row.get("request", {})
        fixture = row.get("fixture_window", {})
        capture = row.get("capture", {})
        if req.get("operation") != "observe" or req.get("target_name") != "fixture":
            raise ValueError("request operation/target mismatch: "+route)
        if req.get("frame") != "window_client" or req.get("region") != EXPECTED_REGION:
            raise ValueError("request coordinate binding mismatch: "+route)
        if req.get("native_target_id") != fixture.get("xid"):
            raise ValueError("request target ID does not match fixture: "+route)
        if fixture.get("title") != "route-unit-3561" or [fixture.get("width"), fixture.get("height")] != [500, 260]:
            raise ValueError("fixture identity/geometry mismatch: "+route)
        if capture.get("target") != "fixture" or capture.get("frame") != "window_client":
            raise ValueError("capture target/frame mismatch: "+route)
        if capture.get("region") != EXPECTED_REGION or [capture.get("width"), capture.get("height")] != [500, 260]:
            raise ValueError("capture region/dimensions mismatch: "+route)
        if capture.get("native_window_id") != fixture.get("xid"):
            raise ValueError("captured native ID mismatch: "+route)
        observation = nested_observation(row)
        if observation.get("status") != "returned" or observation.get("input_dispatched") is not False:
            raise ValueError("raw observation not returned/no-input: "+route)
        artifact = observation.get("observation", {}).get("artifact", {})
        if route in ("api", "cli"):
            artifact = observation.get("artifact", {})
        raw_sha = observation.get("sha256")
        if not raw_sha or row.get("raw_pixel_sha256") != raw_sha:
            raise ValueError("raw pixel hash lineage mismatch: "+route)
        if artifact.get("source_raw_sha256") != raw_sha:
            raise ValueError("PNG/raw source hash mismatch: "+route)
        png_path = root/f"{route}.png"
        data = png_path.read_bytes()
        if sha(data) != row.get("png_sha256") or len(data) != row.get("png_bytes"):
            raise ValueError("PNG byte hash/length mismatch: "+route)
        if artifact.get("sha256") != row.get("png_sha256"):
            raise ValueError("PNG artifact hash mismatch: "+route)
        with Image.open(png_path) as image:
            rgb = image.convert("RGB")
            if rgb.size != (500, 260):
                raise ValueError("decoded dimensions mismatch: "+route)
            pixels[route] = rgb.tobytes()
        png_hashes[route] = row["png_sha256"]
        raw_hashes[route] = raw_sha
        if route == "mcp":
            mcp = row["raw_result"]
            if mcp.get("image_mime_type") != "image/png":
                raise ValueError("MCP image block MIME mismatch")
            meta = mcp.get("metadata", {})
            if meta.get("image_status") != "image":
                raise ValueError("MCP response did not return an image block")
            active = mcp.get("server_pids_during_call", [])
            if not active:
                raise ValueError("MCP server process not observed during call")
            if mcp.get("server_pids_after_close") != []:
                raise ValueError("MCP stdio child remained after close")
    if len(set(pixels.values())) != 1:
        raise ValueError("decoded RGB pixels differ across transports")
    if len(set(raw_hashes.values())) != 1:
        raise ValueError("raw X11 pixel hashes differ across transports")
    return {"audit": "PASS", "decision": "PASS_UNIT_ROUTE_EQUIVALENCE",
            "routes": list(EXPECTED_ROUTES), "pixel_bytes": len(next(iter(pixels.values()))),
            "raw_pixel_sha256": raw_hashes, "png_sha256": png_hashes,
            "rgb_pixels_equal": True, "raw_pixel_hashes_equal": True,
            "input_dispatched": False, "cleanup": "PASS"}


if __name__ == "__main__":
    print(json.dumps(audit(sys.argv[1]), sort_keys=True))
