"""Single-shot JSON runner for observation-only formal scoring."""

import gzip
import json
import sys

from candidate import (GROWTH_THRESHOLDS, PIXEL_THRESHOLDS, TTC_THRESHOLDS_S,
                       analyze)


CANDIDATE_SCHEMA = "looming-image-only-candidate-raw-a04-v1"
OBSERVATION_SCHEMA = "looming-image-only-observations-a02-v1"


def run(observations):
    if type(observations) is not dict or observations.get("schema") != OBSERVATION_SCHEMA:
        raise ValueError("observation_schema_mismatch")
    sequences = observations.get("sequences")
    if type(sequences) is not list or len(sequences) != 13:
        raise ValueError("observation_sequence_count_mismatch")
    outputs = [analyze(sequence) for sequence in sequences]
    if len({row["sequence_id"] for row in outputs}) != len(outputs):
        raise ValueError("duplicate_sequence_id")
    return {"schema": CANDIDATE_SCHEMA, "frame_budget_per_sequence": 5,
            "thresholds": {"pixel": PIXEL_THRESHOLDS,
                           "growth": GROWTH_THRESHOLDS,
                           "ttc": TTC_THRESHOLDS_S},
            "sequences": outputs}


def _read_json(path):
    opener = gzip.open if path.endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as stream:
        return json.load(stream)


def main(source_path, output_path):
    result = run(_read_json(source_path))
    with open(output_path, "w", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, sort_keys=True, separators=(",", ":"))
        stream.write("\n")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: runner.py OBSERVATIONS.json[.gz] RAW_OUTPUT.json")
    main(sys.argv[1], sys.argv[2])
