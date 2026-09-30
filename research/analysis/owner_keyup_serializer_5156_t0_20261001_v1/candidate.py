import json
import sys
from pathlib import Path

from serialize_release import join_explicit_release


def run(source_path, output_path):
    inputs = json.loads(Path(source_path).read_text(encoding="utf-8"))
    rows = [join_explicit_release(item["owner_row"], item["caller_context"]) for item in inputs]
    Path(output_path).write_text(
        "".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )
    return {"decision": "PASS_SERIALIZER_CONSTRUCTION_ONLY", "rows_emitted": len(rows)}


if __name__ == "__main__":
    result = run(sys.argv[1], sys.argv[2])
    print(json.dumps(result, sort_keys=True))
