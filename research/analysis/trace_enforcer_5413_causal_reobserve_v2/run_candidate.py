import gzip
import itertools
import json
from pathlib import Path

from candidate import ALPHABET, execute_trace


root = Path(__file__).resolve().parent
raw_path = root / "raw.jsonl.gz"
count = 0
with raw_path.open("wb") as target:
    with gzip.GzipFile(fileobj=target, mode="wb", filename="", mtime=0, compresslevel=9) as zipped:
        for length in range(7):
            for trace in itertools.product(ALPHABET, repeat=length):
                row = execute_trace(trace)
                zipped.write((json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8"))
                count += 1
print(json.dumps({"allocation": "trace-causal-reobserve-5413-20261001-02",
                  "trace_count": count, "max_trace_length": 6,
                  "raw": raw_path.name}, sort_keys=True))
