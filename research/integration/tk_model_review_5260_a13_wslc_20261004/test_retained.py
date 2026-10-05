import importlib.util
import json
from pathlib import Path
import unittest
from model_contract import parse

class RetainedTests(unittest.TestCase):
    def test_first_real_usage_still_stops_frozen_parser(self):
        root=Path(__file__).resolve().parent
        rows=[json.loads(v) for v in (root/'retained/review01-model-data/row-000/stdout.bin').read_bytes().splitlines()]
        with self.assertRaisesRegex(ValueError,'usage'):parse(rows)

    def test_additive_usage_description_never_promotes_formal_stop(self):
        self.assertIsNotNone(importlib.util.find_spec('verify_packet'),'retained STOP verifier missing')
        from verify_packet import describe_first
        root=Path(__file__).resolve().parent
        rows=[json.loads(v) for v in (root/'retained/review01-model-data/row-000/stdout.bin').read_bytes().splitlines()]
        result=describe_first(rows)
        self.assertEqual(result['usage']['input_tokens'],13710)
        self.assertEqual(result['usage']['reasoning_output_tokens'],32)
        self.assertEqual(result['formal_hypothesis'],'UNQUALIFIED')
        self.assertEqual(result['response']['decision'],'NO_REPAIR')
        changed=json.loads(json.dumps(rows));changed[-1]['usage']['cache_write_input_tokens']=True
        with self.assertRaises(ValueError):describe_first(changed)

if __name__=='__main__':unittest.main()
