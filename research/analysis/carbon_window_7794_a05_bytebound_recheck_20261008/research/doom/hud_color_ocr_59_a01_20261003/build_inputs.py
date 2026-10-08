"""Build image-only candidate inputs and separately concealed source mapping."""
import hashlib
import json
import random
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parents[2] / "research/doom/results/map01-v39-coast-liveness-live-01/runtime"
EVENTS_SHA = "2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381"
PILOT = {37,62,76,81,90,97,103,115,144,154,167,193,200,218}
CROP = (423,591,501,629)
def digest(data): return hashlib.sha256(data).hexdigest()

assert digest((SOURCE/"events.jsonl").read_bytes()) == EVENTS_SHA
events = [json.loads(line) for line in (SOURCE/"events.jsonl").read_text().splitlines()]
typed = [row for row in events if row.get("event") == "typed_observation"]
observations = {row["sequence"]: row for row in events if row.get("event") == "observation"}
assert len(typed) == len(observations) == 218
(ROOT/"input").mkdir(exist_ok=False)
truth = {}
for phase in ("pilot", "evaluation"):
    output = ROOT/"input"/phase
    output.mkdir()
    rows = [row for row in typed if (row["sequence"] in PILOT) == (phase == "pilot")]
    random.Random(59031003).shuffle(rows)
    manifest=[]
    mapping=[]
    for event in rows:
        sequence=event["sequence"]
        image_file=Path(observations[sequence]["image"]).name
        image_path=SOURCE/image_file
        with Image.open(image_path) as loaded:
            image=loaded.convert("RGB")
            assert digest(image.tobytes()) == event["frame_rgb_sha256"] == observations[sequence]["frame_rgb_sha256"]
            crop=image.crop(CROP)
        opaque="i"+digest(f"59031003:{sequence}".encode())[:16]
        crop_path=output/f"{opaque}.png"
        crop.save(crop_path)
        crop_sha=digest(crop_path.read_bytes())
        manifest.append({"id":opaque,"image":crop_path.name,"sha256":crop_sha})
        mapping.append({"id":opaque,"sequence":sequence,"image_file":image_file,"source_file_sha256":digest(image_path.read_bytes()),"crop_sha256":crop_sha,"reference_health":event["signals"]["health"]["value"]})
    (output/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    truth[phase]=mapping
with (ROOT/"TRUTH.json").open("x") as stream:
    json.dump({"events_sha256":EVENTS_SHA,"crop_xyxy":list(CROP),"phases":truth},stream,indent=2)
    stream.write("\n")
print(json.dumps({"pilot":len(truth["pilot"]),"evaluation":len(truth["evaluation"])}))
