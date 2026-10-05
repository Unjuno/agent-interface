#!/usr/bin/env python3
"""Independent reconstruction of the synthetic #7387 T0 package."""
import argparse
import hashlib
import json
import pathlib
import re

BG = (240, 240, 240)
COLORS = {
    "red_square": (220, 30, 30), "blue_disk": (20, 70, 220),
    "green_triangle": (20, 170, 60), "purple_cross": (160, 30, 180),
}


def expected_ppm(cue, width, height):
    data = bytearray()
    for row in range(height):
        for col in range(width):
            x, y = col - width // 2, row - height // 2
            inside = False
            canvas = 8 <= col < 24 and 8 <= row < 24
            if cue == "red_square":
                inside = canvas and -8 <= x < 8 and -8 <= y < 8
            elif cue == "blue_disk":
                inside = canvas and x*x + y*y <= 56
            elif cue == "green_triangle":
                inside = canvas and -8 <= y <= 7 and 2*abs(x) <= y + 9
            elif cue == "purple_cross":
                inside = canvas and ((abs(x) <= 2 and abs(y) <= 8) or (abs(y) <= 2 and abs(x) <= 8))
            data.extend(COLORS[cue] if inside else BG)
    return f"P6\n{width} {height}\n255\n".encode("ascii") + bytes(data)


def token_for(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:24]


def read_lines(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def parse_ppm(blob, width, height):
    header = f"P6\n{width} {height}\n255\n".encode("ascii")
    if not blob.startswith(header) or len(blob) != len(header) + width*height*3:
        raise ValueError("invalid PPM header/dimension/payload")
    return blob[len(header):]


def audit_package(outdir, design_override=None):
    outdir = pathlib.Path(outdir)
    design_path = pathlib.Path(__file__).with_name("design.json")
    design = design_override if design_override is not None else json.loads(design_path.read_text(encoding="utf-8"))
    errors = []
    try:
        manifest = read_lines(outdir / "presentations.jsonl")
        isolated = read_lines(outdir / "isolated.jsonl")
        oracle = json.loads((outdir / "oracle.json").read_text(encoding="utf-8"))
    except Exception as exc:
        return {"ok": False, "errors": [f"read:{type(exc).__name__}:{exc}"]}

    expected = {}
    for lag in design["lags"]:
        for t2 in design["t2_positions"]:
            t1 = t2 - lag
            for first, second in design["ordered_pairs"]:
                tok = token_for(f"7387-t0|{lag}|{t2}|{first}|{second}")
                if t1 < 0 or t1 >= t2 or first == second or first not in COLORS or second not in COLORS:
                    errors.append("design-invalid")
                frame_cues = [None] * design["frame_count"]
                frame_cues[t1], frame_cues[t2] = first, second
                paths = ["images/" + token_for(f"{tok}|{i}") + ".ppm" for i in range(design["frame_count"])]
                expected[tok] = {"lag": lag, "t1": t1, "t2": t2, "cue1": first,
                                 "cue2": second, "cues": frame_cues, "frames": paths}
    expected_iso = {}
    for cue in design["cues"]:
        for pos in design["isolated_positions"]:
            tok = token_for(f"7387-t0|isolated|{cue}|{pos}")
            cues = [None] * design["frame_count"]
            cues[pos] = cue
            expected_iso[tok] = {"cue": cue, "pos": pos, "cues": cues,
                                 "frames": ["images/" + token_for(f"{tok}|{i}") + ".ppm" for i in range(design["frame_count"])]}

    wanted_oracle = [{"token": tok, "lag": e["lag"], "t1": e["t1"], "t2": e["t2"],
                      "cue1": e["cue1"], "cue2": e["cue2"], "frames": e["frames"]}
                     for tok, e in sorted(expected.items())]
    got_oracle = sorted(oracle.get("rows", []), key=lambda x: x.get("token", ""))
    if oracle.get("schema") != design["schema"] or got_oracle != wanted_oracle:
        errors.append("oracle-mismatch")

    expected_rows = {(tok, arm): e for tok, e in expected.items() for arm in design["arms"]}
    if len(manifest) != len(expected_rows):
        errors.append("presentation-denominator")
    seen = set()
    for row in manifest:
        key = (row.get("token"), row.get("arm"))
        e = expected_rows.get(key)
        if e is None or key in seen:
            errors.append("presentation-key-or-duplicate")
            continue
        seen.add(key)
        expected_prompt = ("Identify both changed symbols and their source frame indices." if key[1] == "DUAL_REQUIRED"
                           else "Identify only the second changed symbol and its source frame index.")
        if row.get("prompt") != expected_prompt:
            errors.append("arm-prompt-mapping")
        if row.get("frames") != e["frames"] or row.get("source_indices") != list(range(design["frame_count"])):
            errors.append("frame-order-or-source-index")
        if any(label in " ".join(row.get("frames", [])) + row.get("prompt", "") for label in COLORS):
            errors.append("answer-metadata-leak")
    if seen != set(expected_rows):
        errors.append("presentation-coverage")

    iso_seen = set()
    if len(isolated) != len(expected_iso):
        errors.append("isolated-denominator")
    for row in isolated:
        tok = row.get("token")
        e = expected_iso.get(tok)
        if e is None or tok in iso_seen:
            errors.append("isolated-key-or-duplicate")
            continue
        iso_seen.add(tok)
        if row.get("frames") != e["frames"] or row.get("source_indices") != list(range(design["frame_count"])):
            errors.append("isolated-frame-order")
        if row.get("prompt") != "Identify the one changed symbol and its source frame index.":
            errors.append("isolated-prompt")
    if iso_seen != set(expected_iso):
        errors.append("isolated-coverage")

    image_count = 0
    wanted_paths = {p for e in expected.values() for p in e["frames"]} | {p for e in expected_iso.values() for p in e["frames"]}
    for path in sorted(wanted_paths):
        try:
            blob = (outdir / path).read_bytes()
            # Resolve event role from the independently reconstructed design, not filename text.
            cue = None
            for e in expected.values():
                if path in e["frames"]:
                    cue = e["cues"][e["frames"].index(path)]
                    break
            if cue is None:
                for e in expected_iso.values():
                    if path in e["frames"]:
                        cue = e["cues"][e["frames"].index(path)]
                        break
            if blob != expected_ppm(cue, design["width"], design["height"]):
                errors.append(f"pixel-or-cue-mismatch:{path}:{cue}")
            parse_ppm(blob, design["width"], design["height"])
            image_count += 1
        except Exception as exc:
            errors.append(f"image-read:{type(exc).__name__}")

    sum_file = outdir / "SHA256SUMS"
    try:
        entries = {}
        for line in sum_file.read_text(encoding="ascii").splitlines():
            digest, rel = line.split("  ", 1)
            entries[rel] = digest
        actual = {p.relative_to(outdir).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in outdir.rglob("*") if p.is_file() and p.name not in {"SHA256SUMS", "audit.json"}}
        if entries != actual:
            errors.append("sha256-manifest-mismatch")
    except Exception as exc:
        errors.append(f"sha256-manifest-read:{type(exc).__name__}")
    return {"ok": not errors, "errors": sorted(set(errors)), "matched_trials": len(expected),
            "presentation_rows": len(manifest), "isolated_controls": len(isolated), "unique_images": image_count,
            "method_scope_only": True}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True)
    args = p.parse_args()
    result = audit_package(args.out)
    (pathlib.Path(args.out) / "audit.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
