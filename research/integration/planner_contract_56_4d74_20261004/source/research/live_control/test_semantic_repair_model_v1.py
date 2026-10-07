import unittest
from pathlib import Path
from research.live_control.semantic_repair_model_v1 import parse_output

ROOT=Path(__file__).resolve().parent
HISTORICAL=ROOT/"results/compiled-gui-interface-live-05/2-positive/grounding-model"

class SemanticRepairModelTests(unittest.TestCase):
    def test_historical_luna_turn_parses_with_usage(self):
        result=parse_output(HISTORICAL)
        self.assertEqual(result["grounding"]["field_point"],[180,243])
        self.assertEqual(result["grounding"]["submit_point"],[270,243])
        self.assertGreater(result["usage"]["input_tokens"],0)
        self.assertEqual(result["requested_model"],"gpt-5.6-luna")

if __name__=="__main__":unittest.main()
