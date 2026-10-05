import json
import sys
from pathlib import Path


def classify(image):
    receipt = image.get("receipt")
    effect = image.get("effect")
    valid = image.get("receipt_bytes_valid")
    if valid is False or receipt == "TORN":
        return "CORRUPT_OR_UNTRUSTED"
    if (valid is not True or receipt not in {"DONE", "NOT_STARTED", "ABSENT", "PENDING"}
            or effect not in {"CONFIRMED", "NO_EFFECT_CONFIRMED", "UNKNOWN"}):
        return "CORRUPT_OR_UNTRUSTED"
    if effect == "CONFIRMED" and receipt == "DONE":
        return "EFFECT_AND_RECEIPT_CONFIRMED"
    if effect == "NO_EFFECT_CONFIRMED" and receipt in {"NOT_STARTED", "ABSENT"}:
        return "NO_EFFECT_CONFIRMED"
    return "UNKNOWN_RECONCILE"


def evaluate(fixture):
    rows = []
    for scenario in fixture["scenarios"]:
        for model, key in (("PROCESS", "process_images"), ("MACHINE", "machine_images")):
            for index, image in enumerate(scenario[key]):
                rows.append({
                    "scenario": scenario["id"],
                    "model": model,
                    "image_index": index,
                    "image": image,
                    "classification": classify(image),
                })
    return rows


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: candidate.py FIXTURE.json OUTPUT.json")
    fixture_path, output_path = map(Path, sys.argv[1:])
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    rows = evaluate(fixture)
    Path(output_path).write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"rows": len(rows), "output": str(output_path)}, sort_keys=True))


if __name__ == "__main__":
    main()
