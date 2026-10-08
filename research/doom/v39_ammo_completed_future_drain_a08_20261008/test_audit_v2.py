import copy
import json
import unittest
from pathlib import Path
from .audit_v2 import validate_result

HERE=Path(__file__).resolve().parent

class CompletedFutureAuditV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result=json.loads((HERE/'RESULT.json').read_text(encoding='utf-8'))
        cls.events=[json.loads(line) for line in (HERE/'events.jsonl').read_text(encoding='utf-8').splitlines()]

    def test_baseline_rederives_order_from_frozen_ast(self):
        self.assertTrue(validate_result(self.result,self.events))

    def test_mutated_reported_source_lines_rejected(self):
        result=copy.deepcopy(self.result)
        result['main_order_lines']['drain'] += 1
        with self.assertRaisesRegex(ValueError,'differ from frozen AST'):
            validate_result(result,self.events)

    def test_ordered_but_wrong_line_claim_rejected(self):
        result=copy.deepcopy(self.result)
        result['main_order_lines']={'drain':1,'planner_result':2,'final_admission':3}
        with self.assertRaisesRegex(ValueError,'differ from frozen AST'):
            validate_result(result,self.events)

if __name__=='__main__':
    unittest.main(verbosity=2)
