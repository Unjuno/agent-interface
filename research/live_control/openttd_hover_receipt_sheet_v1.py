"""Pack a source frame and bounded-batch hover evidence for one model call."""
from pathlib import Path

from PIL import Image, ImageDraw


def build(source_image, batches, runtime_dir, destination):
    runtime_dir = Path(runtime_dir)
    with Image.open(Path(source_image)) as opened:
        source = opened.convert("RGB")
    rows = []
    for batch in batches:
        observations = {row["step"]: row for row in batch["records"]
                        if row.get("event") == "observation"}
        for index, point in enumerate(batch["points"]):
            observation = observations[index * 3 + 1]
            rows.append((point, runtime_dir / Path(observation["image"]).name))
    strip_height = 125
    sheet = Image.new("RGB", (source.width, source.height + strip_height * len(rows)),
                      "black")
    sheet.paste(source, (0, 0))
    draw = ImageDraw.Draw(sheet)
    for index, (point, image_path) in enumerate(rows):
        with Image.open(image_path) as opened:
            frame = opened.convert("RGB")
        y = source.height + index * strip_height
        sheet.paste(frame.crop((0, 30, source.width, 145)), (0, y + 10))
        draw.rectangle((0, y, 205, y + 18), fill="black")
        draw.text((5, y + 3), f"hover {index + 1}: {tuple(point)}", fill="white")
    sheet.save(Path(destination))
    return Path(destination)
