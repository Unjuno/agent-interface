"""Postformal lossless codec. Decode stored data; never run RNG or policy."""
import base64
import hashlib
import itertools
import json
import lzma
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent


def restore(destination, root=ROOT):
    destination = Path(destination)
    if destination.exists():
        raise ValueError("destination exists")
    pack = json.loads((root / "PACK.json").read_text())
    if pack["schema"] != "lossless-raw-column-codec-v1" or pack["row_count"] != 8997 or pack["columns"] != 12:
        raise ValueError("codec shape")
    encoded = []
    for index, item in enumerate(pack["parts"]):
        if item["name"] != f"RAW.columns.part{index:02d}.b64":
            raise ValueError("part order/name")
        data = (root / item["name"]).read_bytes()
        if len(data) != item["bytes"] or hashlib.sha256(data).hexdigest() != item["sha256"]:
            raise ValueError("part integrity")
        encoded.append(data)
    compressed = base64.b64decode(b"".join(encoded), validate=True)
    if len(compressed) != pack["compressed_bytes"] or len(compressed) > 200000 or hashlib.sha256(compressed).hexdigest() != pack["compressed_sha256"]:
        raise ValueError("compressed integrity")
    decoder = lzma.LZMADecompressor(memlimit=128*1024*1024)
    columns = decoder.decompress(compressed, max_length=107965)
    if len(columns) != 107964 or not decoder.eof or decoder.unused_data or hashlib.sha256(columns).hexdigest() != pack["encoded_sha256"]:
        raise ValueError("column integrity")
    n = 8997
    permutations = list(itertools.permutations([3,2,1,0]))
    cursor = 0
    def row(evaluation):
        nonlocal cursor
        if cursor >= n:
            raise ValueError("too many rows")
        fields = [columns[c*n+cursor] for c in range(12)]
        cursor += 1
        if any(v>=100 for v in fields[:4]) or fields[4]>=24 or any(v>=16 for v in fields[9:]):
            raise ValueError("encoded field range")
        z = list(permutations[fields[4]])
        result = {"u":fields[:4],"z":z,"s":[z[i]+fields[5+i] for i in range(4)]}
        if evaluation:
            result["sets"] = {arm:[i for i in range(4) if fields[9+j] & (1<<i)]
                              for j,arm in enumerate(("TOP1_POINT","MARGINAL95","JOINT95"))}
        return result
    raw = pack["skeleton"]
    for block in raw["blocks"]:
        if block["calibration"] != 999:
            raise ValueError("calibration denominator")
        block["calibration"] = [row(False) for _ in range(999)]
        for profile in block["profiles"]:
            if profile["rows"] != 1000:
                raise ValueError("evaluation denominator")
            profile["rows"] = [row(True) for _ in range(1000)]
    if cursor != n:
        raise ValueError("remaining rows")
    result = json.dumps(raw,sort_keys=True,separators=(",",":"),allow_nan=False).encode()
    if len(result) != pack["raw_bytes"] or hashlib.sha256(result).hexdigest() != pack["raw_sha256"]:
        raise ValueError("restored raw integrity")
    with destination.open("xb") as handle:
        handle.write(result)
    return {"bytes":len(result),"sha256":hashlib.sha256(result).hexdigest()}

if __name__ == "__main__":
    print(json.dumps(restore(sys.argv[1]),sort_keys=True))
