"""Independent, transport-agnostic audit of one retained #3548 allocation."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import tarfile
import io

from PIL import Image
import io


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def audit(root: Path) -> dict:
    root = root.resolve()
    manifest_path = root / "raw-sha256.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    actual = {p.relative_to(root).as_posix(): sha(p.read_bytes())
              for p in sorted(root.rglob("*")) if p.is_file() and p != manifest_path}
    rows = json.loads((root / "comparison.json").read_text(encoding="utf-8"))
    expected = ["api", "cli", "mcp"]
    experiment = json.loads((root / "experiment-manifest.json").read_text(encoding="utf-8"))
    repo = Path("/repo")
    # The audit is intended to validate historical provenance after integration.
    # Compare against the frozen experiment commit, not the current checkout,
    # which may legitimately contain later changes to measured source files.
    frozen_root = Path("/frozen-source")
    source_hashes_match = all(
        (frozen_root / name).is_file() and
        hashlib.sha256((frozen_root / name).read_bytes()).hexdigest() == digest
        for name, digest in experiment["source_sha256"].items())
    checks = {"manifest_matches": actual == manifest,
              "exactly_three_routes": [r["route"] for r in rows] == expected,
              "source_hashes_match": source_hashes_match,
              "frozen_source_commit": len(experiment["source_commit"]) == 40,
              "frozen_experiment_commit": len(experiment["experiment_commit"]) == 40,
              "runtime_isolated": experiment["runtime_network"] == "none" and
                  experiment["input_actions"] == 0 and experiment["model_calls"] == 0,
              "mcp_version_pinned": experiment["versions"]["mcp"] == "1.30.0",
              "linux_arm64": experiment["platform"] == "aarch64"}
    for row in rows:
        route = row["route"]
        checks[f"{route}_returned_capture"] = row["status"] == "returned" and row["image_status"] == "image"
        checks[f"{route}_no_authority"] = (row["side_effect_authority"] is False and
            row["input_dispatched"] is False)
        checks[f"{route}_request_semantics"] = (row["request"]["target"] == "fixture" and
            row["request"]["frame"] == "window_client" and row["request"]["region"] == [0, 0, 500, 260])
        checks[f"{route}_capture_matches_request"] = (row["observation"]["target"] == row["request"]["target"] and
            row["observation"]["native_window_id"] == row["request"]["native_window_id"] and
            row["observation"]["frame"] == row["request"]["frame"] and
            row["observation"]["region"] == row["request"]["region"] and
            row["observation"]["width"] == 500 and row["observation"]["height"] == 260 and
            row["observation"]["artifact_source_raw_sha256"] == row["observation"]["raw_pixel_sha256"])
        png = (root / route / "image.png").read_bytes()
        with Image.open(io.BytesIO(png)) as image:
            pixels = image.convert("RGB").tobytes()
            dimensions = list(image.size)
        checks[f"{route}_image_hashes"] = (sha(png) == row["png_sha256"] and
            sha(pixels) == row["pixel_sha256"] and
            dimensions == row["dimensions"])
        checks[f"{route}_fixture_reaped"] = row["process"]["fixture"]["exit_code"] == -15
        checks[f"{route}_exactly_one_attempt"] = row["attempt_count"] == 1
        if route == "cli":
            checks["cli_exit_zero"] = (row["process"].get("exit_code") == 0 and
                (root / "cli/exit-code.txt").read_text().strip() == "0" and
                not (root / "cli/stderr.txt").read_text().strip())
    checks["matching_pixel_hashes"] = len({r["pixel_sha256"] for r in rows}) == 1
    checks["matching_dimensions"] = len({tuple(r["dimensions"]) for r in rows}) == 1
    checks["mcp_exposes_observe"] = "interface_observe" in rows[2]["process"]["tool_names"]
    mcp_blocks = json.loads((root / "mcp/mcp-blocks.json").read_text())
    checks["mcp_separate_png_block"] = (not mcp_blocks["is_error"] and
        any(block.get("type") == "image" and block.get("mimeType") == "image/png"
            for block in mcp_blocks["blocks"]))
    checks["mcp_image_block_matches_png"] = any(
        block.get("type") == "image" and block.get("data_sha256") == rows[2]["png_sha256"]
        for block in mcp_blocks["blocks"])
    checks["mcp_child_identified_and_reaped"] = (
        rows[2]["process"]["pid"] is not None and
        rows[2]["process"]["child_reaped_after_transport_close"] is True)
    report = {"disposition": "PASS_UNIT_ROUTE_EQUIVALENCE" if all(checks.values()) else "FAIL_AUDIT",
        "scope": "one no-input X11 observation across public API, CLI and stdio MCP; no model/task or efficiency claim",
        "evidence_root": str(root), "checks": checks,
        "routes": [{"route": r["route"], "elapsed_ns": r["elapsed_ns"],
                    "pixel_sha256": r["pixel_sha256"], "png_sha256": r["png_sha256"]} for r in rows]}
    return report


if __name__ == "__main__":
    result = audit(Path(sys.argv[1]))
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if len(sys.argv) == 4 and sys.argv[2] == "--output":
        output = Path(sys.argv[3]).resolve()
        root = Path(sys.argv[1]).resolve()
        try:
            output.relative_to(root)
        except ValueError:
            pass
        else:
            raise SystemExit("audit output must be outside immutable allocation")
        output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    raise SystemExit(0 if result["disposition"].startswith("PASS_") else 1)
