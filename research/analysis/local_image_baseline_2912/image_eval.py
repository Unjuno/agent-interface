import json, math
from pathlib import Path
from PIL import Image

MANIFEST = Path("/data/manifest.json")
ROOT = Path("/data")
METHOD = {"first_action":"enter_exact_token","continue_when":"field_pixels_changed_and_submit_revalidated","second_action":"activate_submit","complete_when":"submission_pixels_changed_then_independent_score"}

def feat(path):
    image = Image.open(path).convert("RGB").resize((16, 10))
    return [value / 255.0 for pixel in image.getdata() for value in pixel]

def candidate(layout, coords):
    field, submit = coords[layout]
    def target(point):
        return {"point_space":"source_observation_pixels","point":{"x":point[0],"y":point[1]},"motion_model":"surface_origin_translation"}
    return {"format":"compiled-form-grounding-v1","field":target(field),"submit":target(submit),"method":METHOD}

def valid(value):
    return (set(value) == {"format","field","submit","method"}
            and value["format"] == "compiled-form-grounding-v1"
            and set(value["field"]) == {"point_space","point","motion_model"}
            and set(value["submit"]) == {"point_space","point","motion_model"}
            and value["field"]["point"] != value["submit"]["point"]
            and value["method"] == METHOD)

def distance(left, right):
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(left, right)))

def main():
    manifest = json.loads(MANIFEST.read_text())
    rows = [(record, feat(ROOT / record["image"])) for record in manifest["records"]]
    coords = {record["layout"]: (tuple(record["field_point"]), tuple(record["submit_point"])) for record, _ in rows}
    results = []
    for index, (gold, vector) in enumerate(rows):
        pool = [(record, other) for j, (record, other) in enumerate(rows) if j != index]
        nearest = min(pool, key=lambda item: distance(vector, item[1]))[0]
        prediction = candidate(nearest["layout"], coords)
        results.append({"task_id":gold["task_id"],"gold_layout":gold["layout"],"pred_layout":nearest["layout"],
                        "image_sha256":gold["image_sha256"],"validator_accept":valid(prediction),
                        "exact_layout":gold["layout"] == nearest["layout"]})
    report = {"format":"local-image-feature-baseline-v1","runtime":"docker-cpu",
              "feature":"RGB 16x10 nearest-neighbour","records":len(results),
              "validator_accept":sum(row["validator_accept"] for row in results),
              "exact_layout":sum(row["exact_layout"] for row in results),"results":results,
              "status":"PASS" if all(row["validator_accept"] for row in results) else "STOP",
              "note":"small image-feature baseline; no deep model, no GUI action, no authority"}
    print(json.dumps(report, sort_keys=True))

if __name__ == "__main__":
    main()
