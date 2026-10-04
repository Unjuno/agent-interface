import json
import unittest
from pathlib import Path

from adapter import adapt_session_records


DATA = Path(__file__).resolve().parent / "visual03_a03"


def read_jsonl(name):
    return [json.loads(line) for line in (DATA / name).read_text(encoding="utf-8").splitlines() if line.strip()]


class Visual03AdapterCompositionTests(unittest.TestCase):
    def test_actual_visual03_scoring_and_multistep_input_rows_compose(self):
        result = adapt_session_records(
            read_jsonl("scorer-samples.jsonl"),
            read_jsonl("scorer-events.jsonl"),
            read_jsonl("input-rows.jsonl"),
        )
        self.assertEqual(result["trace_integrity"], "SOURCE_ROWS_JOINED")
        self.assertEqual(result["counts"]["input_admissions"], 19)
        self.assertEqual(result["counts"]["key_release_receipts"], 19)
        self.assertEqual(result["counts"]["scorer_samples"], 761)
        self.assertEqual(result["counts"]["scorer_events"], 1)
        self.assertEqual(result["counts"]["integrity_flags"], [])
        self.assertEqual(len(result["attributions"]), 1)
        attribution = result["attributions"][0]
        self.assertEqual(attribution["status"], "TEMPORALLY_UNIQUE")
        self.assertEqual(attribution["intent_token"], "41a11010ac2d4543bfb8d4f2b4bb8f83")
        self.assertEqual(attribution["detection_interval_ns"], [28348735736, 28398091723])
        self.assertEqual(attribution["causal_attribution"], "NOT_ESTABLISHED")


if __name__ == "__main__":
    unittest.main()
