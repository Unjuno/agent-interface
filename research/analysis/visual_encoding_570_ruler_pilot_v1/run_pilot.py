"""Single-shot local RAW vs border-ruler visual-grounding pilot for Issue #570."""
from __future__ import annotations

import base64
import hashlib
import io
import json
import math
import random
import platform
import subprocess
import time
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results" / "formal01"
WIDTH, HEIGHT = 1280, 800
MODEL = "qwen2.5vl:3b"
MODEL_DIGEST = "fb90415cde1ef08aa669ae74b082d49b158729b6db1ab183c941417d507e71a1"
SEED = 57020260927


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_font(size: int) -> ImageFont.FreeTypeFont:
    candidates = [
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/segoeui.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


def source_case(rng: random.Random, index: int) -> tuple[bytes, dict, str]:
    image = Image.new("RGB", (WIDTH, HEIGHT), "#f1f3f5")
    d = ImageDraw.Draw(image)
    title_font, card_font, small_font = load_font(22), load_font(17), load_font(15)
    d.rectangle((72, 64, 1207, 735), fill="#ffffff", outline="#60656d", width=2)
    d.rectangle((72, 64, 1207, 111), fill="#26364a")
    d.text((94, 76), "Settings", fill="white", font=title_font)
    d.text((1010, 79), "LOCAL DEMO", fill="#d9e5f2", font=small_font)

    categories = ["Privacy", "Network", "Display", "Audio"]
    labels = ["Apply", "Apply", "Apply", "Apply"]
    # Vary panel arrangement and each repeated control's position while keeping
    # all source coordinates recoverable from the retained renderer manifest.
    slots = [(102, 145), (674, 145), (102, 438), (674, 438)]
    rng.shuffle(slots)
    rng.shuffle(categories)
    card_boxes: dict[str, tuple[int, int, int, int]] = {}
    target_boxes: dict[str, tuple[int, int, int, int]] = {}
    for category, (x, y) in zip(categories, slots):
        w, h = 500, 250
        card_boxes[category] = (x, y, x + w, y + h)
        d.rounded_rectangle((x, y, x + w, y + h), radius=8, fill="#fbfcfd", outline="#98a0aa", width=2)
        d.text((x + 18, y + 13), category, fill="#182332", font=card_font)
        d.line((x + 16, y + 47, x + w - 16, y + 47), fill="#d9dde2", width=1)
        d.text((x + 18, y + 68), f"{category} options", fill="#505963", font=small_font)
        d.text((x + 18, y + 99), "Status", fill="#515965", font=small_font)
        d.rounded_rectangle((x + 298, y + 92, x + 448, y + 126), radius=5, fill="#eef1f4", outline="#aab0b8")
        d.text((x + 313, y + 99), "Enabled", fill="#28313b", font=small_font)
        bx = x + rng.choice([36, 170, 304])
        by = y + rng.choice([164, 177, 190])
        box = (bx, by, bx + 124, by + 42)
        target_boxes[category] = box
        d.rounded_rectangle(box, radius=5, fill="#1769aa", outline="#0d4e82", width=1)
        d.text((bx + 36, by + 10), "Apply", fill="white", font=small_font)
        d.rounded_rectangle((x + 18, y + 164, x + 144, y + 206), radius=5, fill="#edf0f3", outline="#b8bec5")
        d.text((x + 51, y + 175), "Cancel", fill="#35404b", font=small_font)

    absent = index in (5, 10)
    target_category = "Security" if absent else categories[index % len(categories)]
    prompt = f"In the Settings window, identify the center of the blue Apply button in the {target_category} panel. Return coordinates normalized to the original 1280x800 screenshot, not the border or any resized view. If that panel/button is absent, abstain."
    truth_box = target_boxes.get(target_category)
    truth = None if truth_box is None else {
        "box": list(truth_box),
        "center": [(truth_box[0] + truth_box[2]) / 2, (truth_box[1] + truth_box[3]) / 2],
        "category": target_category,
    }
    buf = io.BytesIO()
    image.save(buf, format="PNG", optimize=False)
    return buf.getvalue(), {"index": index, "prompt": prompt, "truth": truth, "card_boxes": {k: list(v) for k, v in card_boxes.items()}}, "arial.ttf"


def ruler_view(source: Image.Image) -> Image.Image:
    result = source.copy()
    d = ImageDraw.Draw(result)
    font = load_font(11)
    # The renderer reserves x<72 and y<64 as blank margins. These marks do not
    # overlay or rescale any app pixel and use the exact source pixel axes.
    for x in range(100, WIDTH, 100):
        d.line((x, 45, x, 62), fill="#6b7280", width=1)
        d.text((x - 12, 48), str(x), fill="#303843", font=font)
    for y in range(100, HEIGHT, 100):
        d.line((49, y, 70, y), fill="#6b7280", width=1)
        d.text((4, y - 6), str(y), fill="#303843", font=font)
    return result


def environment_snapshot() -> dict:
    snapshot = {"platform": platform.platform(), "python": platform.python_version(), "pillow": Image.__version__}
    for key, argv in {
        "ollama_version": ["ollama", "--version"],
        "ollama_ps": ["ollama", "ps"],
        "nvidia_smi": ["nvidia-smi", "--query-gpu=name,memory.total,memory.used,utilization.gpu", "--format=csv,noheader"],
    }.items():
        try:
            completed = subprocess.run(argv, capture_output=True, text=True, timeout=15, check=False)
            snapshot[key] = {"exit_code": completed.returncode, "stdout": completed.stdout.strip(), "stderr": completed.stderr.strip()}
        except Exception as exc:
            snapshot[key] = {"error_type": type(exc).__name__, "error": str(exc)}
    return snapshot


def request(model: str, encoded: str, prompt: str, seed: int) -> dict:
    schema = {
        "type": "object",
        "properties": {
            "x_norm": {"type": ["number", "null"]},
            "y_norm": {"type": ["number", "null"]},
            "abstain": {"type": "boolean"},
        },
        "required": ["x_norm", "y_norm", "abstain"],
    }
    payload = {
        "model": model,
        "prompt": prompt + " Return only JSON with x_norm and y_norm as numbers from 0 to 1, or both null if abstaining, and abstain as boolean.",
        "images": [encoded],
        "format": schema,
        "stream": False,
        "options": {"temperature": 0, "seed": seed, "num_predict": 64},
    }
    req = urllib.request.Request(
        "http://127.0.0.1:11434/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = time.perf_counter()
    with urllib.request.urlopen(req, timeout=180) as response:
        body = response.read()
    elapsed_ms = (time.perf_counter() - started) * 1000
    decoded = json.loads(body)
    return {"http_body": decoded, "elapsed_ms": elapsed_ms}


def main() -> None:
    if OUT.exists():
        raise SystemExit(f"STOP_OUTPUT_EXISTS: {OUT}")
    OUT.mkdir(parents=True)
    environment_before = environment_snapshot()
    rng = random.Random(SEED)
    rows = []
    for i in range(12):
        png, meta, font_name = source_case(rng, i)
        source = Image.open(io.BytesIO(png)).convert("RGB")
        ruler = ruler_view(source)
        ruler_buf = io.BytesIO()
        ruler.save(ruler_buf, format="PNG", optimize=False)
        raw_bytes, ruler_bytes = png, ruler_buf.getvalue()
        case_dir = OUT / "cases"
        case_dir.mkdir(exist_ok=True)
        (case_dir / f"{i:02d}_raw.png").write_bytes(raw_bytes)
        (case_dir / f"{i:02d}_ruler.png").write_bytes(ruler_bytes)
        image_hashes = {"RAW": sha(raw_bytes), "BORDER_RULER": sha(ruler_bytes)}
        order = ["RAW", "BORDER_RULER"] if i % 2 == 0 else ["BORDER_RULER", "RAW"]
        calls = {}
        for arm in order:
            arm_bytes = raw_bytes if arm == "RAW" else ruler_bytes
            started = time.time_ns()
            try:
                result = request(MODEL, base64.b64encode(arm_bytes).decode("ascii"), meta["prompt"], SEED + i)
                raw = result["http_body"]
                parsed = json.loads(raw.get("response", "{}"))
                calls[arm] = {
                    "status": "ok",
                    "parsed": parsed,
                    "response": raw,
                    "elapsed_ms": result["elapsed_ms"],
                    "request_image_sha256": image_hashes[arm],
                    "request_started_ns": started,
                }
            except Exception as exc:
                calls[arm] = {"status": "error", "error_type": type(exc).__name__, "error": str(exc), "request_started_ns": started}
                # First transport/model failure is retained; do not retry.
                break
        rows.append({
            "index": i,
            "source_image_sha256": image_hashes["RAW"],
            "arm_image_sha256": image_hashes,
            "prompt": meta["prompt"],
            "truth": meta["truth"],
            "card_boxes": meta["card_boxes"],
            "order": order,
            "font": font_name,
            "calls": calls,
        })
        (OUT / "RAW.jsonl").open("a", encoding="utf-8").write(json.dumps(rows[-1], sort_keys=True) + "\n")
        if any(call.get("status") != "ok" for call in calls.values()):
            break
    result = {
        "schema": "visual-ruler-570-localvlm-raw-v1",
        "model": MODEL,
        "model_digest": MODEL_DIGEST,
        "seed": SEED,
        "environment_before": environment_before,
        "environment_after": environment_snapshot(),
        "rows": rows,
        "run_exit": 0 if len(rows) == 12 and all(len(r["calls"]) == 2 and all(c.get("status") == "ok" for c in r["calls"].values()) for r in rows) else 1,
        "formal_optimizer_steps": 0,
    }
    raw_bytes = (json.dumps(result, sort_keys=True, indent=2) + "\n").encode("utf-8")
    (OUT / "FORMAL_RESULT.json").write_bytes(raw_bytes)
    print(json.dumps({"rows": len(rows), "model": MODEL, "result_sha256": sha(raw_bytes), "output": str(OUT), "exit": result["run_exit"]}))
    if result["run_exit"] != 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
