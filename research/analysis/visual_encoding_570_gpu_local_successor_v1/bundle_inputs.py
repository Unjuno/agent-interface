from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--data", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    pre = json.loads((args.data / "PREFORMAL.json").read_text(encoding="utf-8"))
    records = [*pre["formal_cases"], pre["construction_case"]]
    for case in records:
        image = args.data / case["image_path"]
        encoded = base64.b64encode(image.read_bytes()).decode("ascii")
        path = args.out / f"{case['case_id']}.png.b64"
        path.write_text(encoded + "\n", encoding="ascii")
    print(json.dumps({"screen_count": len(records), "files": [f"{c['case_id']}.png.b64" for c in records]}))


if __name__ == "__main__":
    main()

