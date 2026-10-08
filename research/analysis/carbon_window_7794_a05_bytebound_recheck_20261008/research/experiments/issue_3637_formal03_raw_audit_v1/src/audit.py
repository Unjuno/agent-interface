from __future__ import annotations

import argparse
import hashlib
import inspect
import json
from pathlib import Path
import posixpath
import subprocess
import sys

from PIL import Image, ImageDraw


REPO = Path(__file__).resolve().parents[4]
PREDECESSOR = REPO / "research/experiments/issue_3626_proxy_effect_unit_v3"
OUTPUT = REPO / "research/experiments/issue_3637_formal03_raw_audit_v1/evidence"
FORMAL = PREDECESSOR / "evidence/formal-03"
ARMS = ("ordinary_screenshot", "proxy_image", "structured_proxy", "hybrid")
FRAME_SIZE = (320, 120)
# Fixed label area: includes COUNT and its digit, excludes the button/hover area.
COUNTER_ROI = (108, 18, 205, 46)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_bytes(commit: str, path: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(REPO), "show", f"{commit}:{path}"])


def git_inventory(commit: str, input_prefix: str) -> list[dict[str, object]]:
    listing = subprocess.check_output([
        "git", "-C", str(REPO), "ls-tree", "-r", "-z", commit, "--", input_prefix
    ])
    records: list[dict[str, object]] = []
    for entry in listing.split(b"\0"):
        if not entry:
            continue
        metadata, path_bytes = entry.split(b"\t", 1)
        mode, object_type, object_id = metadata.decode("ascii").split()
        if object_type != "blob":
            continue
        path = path_bytes.decode("utf-8")
        rel = path.removeprefix(input_prefix.rstrip("/") + "/")
        data = subprocess.check_output(["git", "-C", str(REPO), "cat-file", "blob", object_id])
        records.append({"path": rel, "bytes": len(data), "sha256": digest(data), "git_blob": object_id})
    return sorted(records, key=lambda x: str(x["path"]))


def capture_manifest(root: Path, commit: str) -> dict[str, object]:
    prefix = root.relative_to(REPO).as_posix()
    return {"source_commit": commit, "root": prefix, "files": git_inventory(commit, prefix)}


def inventory_differences(expected: list[dict[str, object]], actual: list[dict[str, object]]) -> list[str]:
    errors: list[str] = []
    if actual != expected:
        expected_by_path = {str(x.get("path")): x for x in expected if isinstance(x, dict)}
        actual_by_path = {str(x["path"]): x for x in actual}
        for path in sorted(expected_by_path.keys() - actual_by_path.keys()):
            errors.append(f"missing input artifact: {path}")
        for path in sorted(actual_by_path.keys() - expected_by_path.keys()):
            errors.append(f"unexpected input artifact: {path}")
        for path in sorted(expected_by_path.keys() & actual_by_path.keys()):
            if expected_by_path[path] != actual_by_path[path]:
                errors.append(f"input artifact hash/length mismatch: {path}")
    return errors


def verify_inventory_data(expected: list[dict[str, object]], data_by_path: dict[str, bytes]) -> list[str]:
    expected_oids = {str(item["path"]): item.get("git_blob") for item in expected}
    actual = [
        {"path": path, "bytes": len(data), "sha256": digest(data), "git_blob": expected_oids.get(path)}
        for path, data in sorted(data_by_path.items())
    ]
    missing = [str(item["path"]) for item in expected if str(item.get("path")) not in data_by_path]
    errors = inventory_differences(expected, actual)
    errors.extend(f"missing input artifact: {path}" for path in missing)
    return errors


def verify_manifest(manifest: dict[str, object]) -> list[str]:
    expected = manifest.get("files")
    if not isinstance(expected, list):
        return ["manifest files must be a list"]
    return inventory_differences(expected, git_inventory(str(manifest["source_commit"]), str(manifest["root"])))


def input_bytes(manifest: dict[str, object], rel: str) -> bytes:
    normalized = posixpath.normpath(rel)
    if normalized.startswith("../") or normalized == "..":
        raise ValueError(f"input path escapes predecessor tree: {rel}")
    root = str(manifest["root"])
    path = f"{root}/{normalized}"
    records = {str(x["path"]): x for x in manifest["files"]}
    if normalized not in records:
        raise FileNotFoundError(f"unmanifested predecessor artifact: {normalized}")
    data = git_bytes(str(manifest["source_commit"]), path)
    expected = records[normalized]
    if len(data) != expected["bytes"] or digest(data) != expected["sha256"]:
        raise ValueError(f"Git blob mismatch for predecessor artifact: {normalized}")
    return data


def counter_crop(data: bytes, size: tuple[int, int]) -> bytes:
    width, height = size
    if (width, height) != FRAME_SIZE or len(data) != width * height * 4:
        raise ValueError("unexpected XImage size/length")
    image = Image.frombytes("RGBX", size, data).convert("RGB")
    return image.crop(COUNTER_ROI).tobytes()


def pixel_transition(case: str, before: bytes, after: bytes) -> bool:
    """Classify only the fixed counter ROI; title metadata and button pixels are excluded."""
    if case == "positive":
        return before != after
    if case == "no_effect":
        return before == after
    raise ValueError(f"unsupported visual control case: {case}")


def corruption_controls() -> dict[str, bool]:
    h0, h1 = digest(b"COUNT 0 pixels"), digest(b"COUNT 1 pixels")
    inventory = [{"path": "aux.raw", "bytes": 3, "sha256": digest(b"abc"), "git_blob": "frozen"}]
    tampered = verify_inventory_data(inventory, {"aux.raw": b"xyz"})
    return {
        "hover_only_delta_does_not_pass_positive": not pixel_transition("positive", h0, h0),
        "counter_pixel_delta_breaks_no_effect_control": not pixel_transition("no_effect", h0, h1),
        "unreferenced_artifact_tamper_detected": bool(tampered),
        "window_title_not_consumed_by_pixel_gate": set(inspect.signature(pixel_transition).parameters) == {"case", "before", "after"},
    }


def verify_sidecar_sums(manifest: dict[str, object]) -> list[str]:
    sum_rel = "evidence/formal-03/SHA256SUMS"
    errors: list[str] = []
    for number, line in enumerate(input_bytes(manifest, sum_rel).decode("utf-8").splitlines(), 1):
        fields = line.split(None, 1)
        if len(fields) != 2:
            errors.append(f"SHA256SUMS line {number}: malformed")
            continue
        expected, rel = fields
        try:
            target_rel = posixpath.normpath(posixpath.join("evidence/formal-03", rel))
            data = input_bytes(manifest, target_rel)
        except (ValueError, OSError, FileNotFoundError):
            errors.append(f"SHA256SUMS line {number}: path escapes input root")
            continue
        if digest(data) != expected:
            errors.append(f"SHA256SUMS line {number}: digest mismatch {rel}")
    return errors


def make_contact_sheet(raw: dict[str, object], manifest: dict[str, object], path: Path) -> dict[str, object]:
    panels: list[tuple[str, Image.Image]] = []
    rows = raw["rows"]
    for arm in ARMS:
        for case in ("positive", "no_effect"):
            row = next(r for r in rows if r["arm"] == arm and r["case"] == case)
            for state_name, label in (("initial_state", "before"), ("after_state", "after")):
                state = row[state_name]
                frame_bytes = input_bytes(manifest, f"evidence/formal-03/{state['frame_path']}")
                frame = Image.frombytes("RGBX", tuple(FRAME_SIZE), frame_bytes).convert("RGB")
                panels.append((f"{arm} | {case} | {label}", frame.resize((480, 180))))
    sheet = Image.new("RGB", (1920, 800), "white")
    draw = ImageDraw.Draw(sheet)
    for index, (label, panel) in enumerate(panels):
        x, y = (index % 4) * 480, (index // 4) * 200
        draw.text((x + 6, y + 3), label, fill="black")
        sheet.paste(panel, (x, y + 20))
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(path)
    return {"path": path.relative_to(OUTPUT.parent).as_posix(), "bytes": path.stat().st_size,
            "sha256": digest(path.read_bytes()), "panels": len(panels),
            "ordering": "arms; positive-before, positive-after, no_effect-before, no_effect-after"}


def audit(manifest: dict[str, object], output_dir: Path) -> dict[str, object]:
    errors = verify_manifest(manifest)
    errors.extend(verify_sidecar_sums(manifest))
    raw = json.loads(input_bytes(manifest, "evidence/formal-03/raw.json").decode("utf-8"))
    rows = raw.get("rows", [])
    expected = {(arm, case) for arm in ARMS for case in
                ("positive", "no_effect", "stale_version", "target_replaced", "unavailable", "ambiguous", "macro_failure")}
    identities = {(row.get("arm"), row.get("case")) for row in rows}
    if len(rows) != 28 or identities != expected:
        errors.append("row identity/denominator mismatch")

    referenced: set[str] = set()
    for row in rows:
        for state_name in ("initial_state", "current_state", "after_state"):
            state = row.get(state_name) or {}
            rel = state.get("frame_path")
            if not rel:
                continue
            referenced.add(str(rel).replace("\\", "/"))
            try:
                data = input_bytes(manifest, f"evidence/formal-03/{rel}")
            except (ValueError, OSError):
                errors.append(f"{row.get('row_id')}: unsafe frame path")
                continue
            if len(data) != state.get("frame_bytes") or digest(data) != state.get("frame_sha256"):
                errors.append(f"{row.get('row_id')}: frame hash/length mismatch {rel}")
        event_rel = f"rows/{row.get('row_id')}/fixture-events.jsonl"
        event_data = input_bytes(manifest, f"evidence/formal-03/{event_rel}")
        if digest(event_data) != row.get("fixture_events_sha256"):
            errors.append(f"{row.get('row_id')}: fixture event file mismatch")
        proxy_rel = (row.get("presentation") or {}).get("proxy_image")
        if proxy_rel:
            proxy_data = input_bytes(manifest, f"evidence/formal-03/{proxy_rel}")
            if digest(proxy_data) != row["presentation"].get("proxy_sha256"):
                errors.append(f"{row.get('row_id')}: proxy image mismatch")

    actual_raw = {str(x["path"]).removeprefix("evidence/formal-03/") for x in manifest["files"]
                  if str(x["path"]).startswith("evidence/formal-03/rows/") and str(x["path"]).endswith(".raw")}
    unreferenced = sorted(actual_raw - referenced)
    referenced_raw = sorted(actual_raw & referenced)
    if len(actual_raw) != 76 or len(referenced_raw) != 68 or len(unreferenced) != 8:
        errors.append(f"raw inventory partition mismatch: total={len(actual_raw)}, linked={len(referenced_raw)}, auxiliary={len(unreferenced)}")

    crops: dict[str, dict[str, str]] = {}
    for arm in ARMS:
        crops[arm] = {}
        for case in ("positive", "no_effect"):
            row = next(r for r in rows if r.get("arm") == arm and r.get("case") == case)
            before = counter_crop(input_bytes(manifest, f"evidence/formal-03/{row['initial_state']['frame_path']}"), FRAME_SIZE)
            after = counter_crop(input_bytes(manifest, f"evidence/formal-03/{row['after_state']['frame_path']}"), FRAME_SIZE)
            crops[arm][case + "_before"] = digest(before)
            crops[arm][case + "_after"] = digest(after)
            if not pixel_transition(case, before, after):
                errors.append(f"{arm}: {case} counter-pixel expectation failed")
            if case == "positive" and before == after:
                errors.append(f"{arm}: positive counter-region pixels did not change")
            if case == "no_effect" and before != after:
                errors.append(f"{arm}: no-effect counter-region changed")
    positive_after = {crops[a]["positive_after"] for a in ARMS}
    zero_labels = {crops[a][k] for a in ARMS for k in ("positive_before", "no_effect_before", "no_effect_after")}
    if len(positive_after) != 1:
        errors.append("positive counter-region pixels differ across arms")
    if len(zero_labels) != 1:
        errors.append("zero/no-effect counter-region pixels differ across arms")
    if positive_after & zero_labels:
        errors.append("positive and zero counter-region pixels are indistinguishable")
    controls = corruption_controls()
    if not all(controls.values()):
        errors.append("one or more audit corruption controls escaped")

    output_dir.mkdir(parents=True, exist_ok=True)
    contact = make_contact_sheet(raw, manifest, output_dir / "counter_contact_sheet.png")
    return {
        "decision": "PASS_RAW_AUDIT_SCOPED" if not errors else "HOLD_RAW_AUDIT_INCOMPLETE",
        "input_source_commit": manifest.get("source_commit"),
        "formal_allocation": raw.get("allocation_id"),
        "row_count": len(rows),
        "artifact_file_count": len(manifest.get("files", [])),
        "raw_artifact_count": len(actual_raw),
        "state_referenced_raw_count": len(referenced_raw),
        "auxiliary_raw_count": len(unreferenced),
        "auxiliary_raw_paths": unreferenced,
        "counter_roi_xyxy": list(COUNTER_ROI),
        "counter_crop_sha256": crops,
        "corruption_controls": controls,
        "contact_sheet": contact,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-commit", default="961f14b836e549ca5f6cfb6bf3ef4b470e91b1b5")
    parser.add_argument("--manifest", type=Path, default=OUTPUT / "predecessor_gitblob_manifest.json")
    parser.add_argument("--result", type=Path, default=OUTPUT / "audit_result_gitblob.json")
    parser.add_argument("--capture-manifest", action="store_true",
                        help="one-time capture from the frozen input tree; refuses to overwrite")
    args = parser.parse_args()
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    if args.capture_manifest:
        if args.manifest.exists():
            parser.error(f"refusing to overwrite frozen manifest: {args.manifest}")
        manifest = capture_manifest(PREDECESSOR, args.input_commit)
        args.manifest.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    else:
        if not args.manifest.is_file():
            parser.error("frozen manifest missing; capture it explicitly once from the preregistered input tree")
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    result = audit(manifest, OUTPUT)
    args.result.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["decision"] == "PASS_RAW_AUDIT_SCOPED" else 1


if __name__ == "__main__":
    sys.exit(main())
