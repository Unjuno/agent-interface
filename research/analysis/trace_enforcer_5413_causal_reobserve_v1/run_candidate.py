import itertools
import json
from pathlib import Path

from candidate import ALPHABET, execute_trace


traces = [trace for n in range(5) for trace in itertools.product(ALPHABET, repeat=n)]
rows = [execute_trace(trace) for trace in traces]
raw = {"schema": "issue-5413-causal-reobserve-raw-v1",
       "allocation": "trace-causal-reobserve-5413-20261001-01",
       "source_main": "2197bead5ffa7dc226390becc811913159c8438e",
       "max_trace_length": 4, "alphabet": list(ALPHABET),
       "trace_count": len(rows), "rows": rows}
out = Path(__file__).resolve().parent / "raw.json"
out.write_text(json.dumps(raw, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
print(json.dumps({"trace_count": len(rows), "output": "raw.json"}, sort_keys=True))
