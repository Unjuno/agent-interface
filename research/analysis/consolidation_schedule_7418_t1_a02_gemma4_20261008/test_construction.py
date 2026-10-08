import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import candidate
import auditor


class ConstructionTests(unittest.TestCase):
    def setUp(self):
        self.pkg = Path(__file__).parent
        self.model = json.loads((self.pkg/"episode_ledger.json").read_text())
        self.prompts = json.loads((self.pkg/"prompts.json").read_text())
        self.queries = json.loads((self.pkg/"queries.json").read_text())

    def test_query_and_consolidation_options_are_fixed_and_seeded(self):
        q = candidate.request_body(self.model,self.prompts,{"kind":"query","question":"q","evidence":{}},4201,128)
        c = candidate.request_body(self.model,self.prompts,{"kind":"consolidate","episodes":[],"memory":{"claims":[]}},4201,256)
        self.assertEqual(q["options"],{"seed":4201,"temperature":0.2,"top_p":0.9,"num_ctx":8192,"num_predict":128})
        self.assertEqual(c["options"]["num_predict"],256)
        self.assertEqual(q["format"],"json")
        self.assertIs(q["think"],False)

    def test_frozen_plan_has_three_seeds_and_390_calls(self):
        query_calls=3*4*6*5
        consolidation_calls=3*(6+3+1)
        self.assertEqual(tuple(candidate.SEEDS),(4201,4202,4203))
        self.assertEqual(query_calls,360)
        self.assertEqual(consolidation_calls,30)
        self.assertEqual(query_calls+consolidation_calls,390)
        self.assertEqual([q["id"] for q in self.queries["queries"]],
                         ["q_common_save","q_rare_exception","q_conflict","q_history_delta","q_heldout_conjunction"])

    def test_episode_values_match_byte_copied_t0_source(self):
        source=json.loads((self.pkg/"source_t0_model.json").read_text())
        self.assertEqual(self.model["episodes"],source["episodes"])

    def test_mock_run_raw_rows_and_independent_reconstruction(self):
        def fake_post(_url,payload):
            if "newly verified episodes" in payload["prompt"]:
                response={"claims":[]}
            else:
                response={"classification":"UNKNOWN","answer":None,"source_ids":[]}
            return {"model":"gemma4:latest","response":json.dumps(response),"prompt_eval_count":10,"eval_count":5,"total_duration":1000}
        with tempfile.TemporaryDirectory() as td:
            raw=Path(td)/"raw.jsonl"
            with patch.object(candidate,"load_model_digest",return_value=("test-digest",123)), patch.object(candidate,"post_json",side_effect=fake_post):
                count=candidate.run(self.model,self.prompts,self.queries,raw,"http://127.0.0.1:11434","test-digest")
            self.assertEqual(count,390)
            result=auditor.audit(raw,self.queries,self.model["episodes"],"test-digest")
            self.assertEqual(result["rows"],390)
            self.assertEqual(result["status"],"PASS_METHOD")
            self.assertEqual(result["errors"],[])
            self.assertLess(result["accuracies"]["4201/episodic_only"],1.0)


if __name__ == "__main__": unittest.main()
