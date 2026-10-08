"""Check compact receipt packing against retained formal OpenTTD evidence."""
import copy
import json
from pathlib import Path

from PIL import Image

from openttd_compact_hover_sheet_v1 import build


HERE = Path(__file__).resolve().parent
ROOT = HERE / "results/openttd-active-evidence-pair-02/2-stable-seed991004"
OUT = HERE / "results-local/openttd-compact-hover-sheet-probe.png"


def main():
    result = json.loads((ROOT / "result.json").read_text(encoding="utf-8"))
    readiness = result["hover_readiness"]
    manifest = build(readiness, ROOT / "runtime", OUT)
    assert len(manifest["rows"]) == 5
    assert manifest["size"] == [640, 334]
    assert [row["point"] for row in manifest["rows"]] == [
        [389, 51], [412, 51], [435, 51], [458, 51], [485, 51]]
    with Image.open(OUT) as image:
        assert list(image.size) == manifest["size"]
    corrupt = copy.deepcopy(readiness)
    corrupt["receipts"][0]["tooltip"]["pixels_sha256"] = "0" * 64
    try:
        build(corrupt, ROOT / "runtime", OUT.with_name("invalid.png"))
    except ValueError as error:
        assert str(error) == "receipt tooltip pixels do not match runtime observation"
    else:
        raise AssertionError("corrupt receipt pixels were accepted")
    print(json.dumps({"rows": 5, "size": manifest["size"],
                      "pixels_sha256": manifest["pixels_sha256"],
                      "corrupt_receipt_refused": True}))


if __name__ == "__main__":
    main()
