"""Retain compact, independently auditable evidence from the frozen v23 run."""
import hashlib
import json
import shutil
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SOURCE = REPO / "results-local/doom/map01-cover-threat-v23-live-02"
TARGET = HERE / "results/map01-cover-threat-v23-live-02"
ROI = (440, 585, 535, 635)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def copy(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)


def main():
    if TARGET.exists():
        raise FileExistsError(TARGET)
    TARGET.mkdir(parents=True)
    report = json.loads((SOURCE / "report.json").read_text())
    events = [json.loads(line) for line in (SOURCE / "runtime/events.jsonl").read_text().splitlines()]
    copy(SOURCE / "report.json", TARGET / "report.json")
    copy(SOURCE / "stderr.txt", TARGET / "stderr.txt")
    for path in (SOURCE / "runtime").iterdir():
        if path.is_file() and path.suffix in {".json", ".jsonl", ".txt", ".ini"}:
            copy(path, TARGET / "runtime" / path.name)
    shutil.copytree(SOURCE / "decision-0", TARGET / "decision-0")
    for index in range(1, len(report["decisions"])):
        shutil.copytree(SOURCE / f"decision-{index}", TARGET / f"decision-{index}")

    decision_frames = []
    for decision in report["decisions"]:
        index = decision["iteration"]
        source = SOURCE / "runtime" / Path(decision["source_image"]).name
        target = TARGET / "frames" / f"decision-{index:02d}.png"
        copy(source, target)
        decision_frames.append({"iteration": index, "original": source.name,
                                "retained": str(target.relative_to(TARGET)).replace("\\", "/"),
                                "sha256": sha(target)})

    roi_index = []
    for row in events:
        if row.get("event") != "observation" or not str(row.get("id", "")).startswith("cover-"):
            continue
        source = SOURCE / "runtime" / Path(row["image"]).name
        with Image.open(source) as opened:
            crop = opened.convert("RGB").crop(ROI)
        name = f"{row['id'].replace('/', '_')}-sequence-{row['sequence']:04d}.png"
        target = TARGET / "health-roi" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        crop.save(target, compress_level=9)
        roi_index.append({
            "id": row["id"], "sequence": row["sequence"],
            "capture_ns": row["capture_ns"], "source_image": source.name,
            "retained": str(target.relative_to(TARGET)).replace("\\", "/"),
            "sha256": sha(target),
        })
    (TARGET / "health-roi-index.json").write_text(
        json.dumps({"box": list(ROI), "rows": roi_index}, indent=2) + "\n",
        encoding="utf-8", newline="\n")
    (TARGET / "decision-frame-index.json").write_text(
        json.dumps(decision_frames, indent=2) + "\n", encoding="utf-8", newline="\n")

    full = Image.new("RGB", (642 * 3, 542 * 4), "black")
    hud = Image.new("RGB", (1060, 200 * len(decision_frames)), "black")
    for item in decision_frames:
        index = item["iteration"]
        with Image.open(TARGET / item["retained"]) as opened:
            image = opened.convert("RGB")
        game = image.crop((320, 162, 962, 663))
        x = (index % 3) * 642; y = (index // 3) * 542
        full.paste(game, (x, y + 40)); ImageDraw.Draw(full).text((x + 8, y + 8), str(index), fill="white")
        crop = image.crop((320, 580, 820, 665)).resize((1000, 170), Image.Resampling.NEAREST)
        hud.paste(crop, (60, index * 200 + 30)); ImageDraw.Draw(hud).text((10, index * 200 + 10), str(index), fill="white")
    full.save(TARGET / "decision-contact-sheet.png", compress_level=9)
    hud.save(TARGET / "hud-contact-sheet.png", compress_level=9)

    files = []
    for path in sorted(TARGET.rglob("*")):
        if path.is_file() and path.name != "retention-manifest.json":
            files.append({"path": str(path.relative_to(TARGET)).replace("\\", "/"),
                          "bytes": path.stat().st_size, "sha256": sha(path)})
    manifest = {
        "schema": "map01-cover-threat-v23-retention-v1",
        "allocation_id": "map01-cover-threat-v23-live-02",
        "source": str(SOURCE.relative_to(REPO)).replace("\\", "/"),
        "selection": "all model-call directories and runtime metadata/events; exact decision frames; lossless health ROI for every cover observation; no full raw observation stream or AIT packets",
        "files": files,
        "total_files": len(files),
        "total_bytes": sum(row["bytes"] for row in files),
    }
    (TARGET / "retention-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"target": str(TARGET.relative_to(REPO)),
                      "files": manifest["total_files"],
                      "bytes": manifest["total_bytes"],
                      "roi_observations": len(roi_index)}, indent=2))


if __name__ == "__main__":
    main()
