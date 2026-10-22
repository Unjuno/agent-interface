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
        q = candidate.request_body(self.model,self.prompts,{"kind":"query","question":"q","evidence":{}},5001,128)
        c = candidate.request_body(self.model,self.prompts,{"kind":"consolidate","episodes":[],"memory":{"claims":[]}},5001,2048)
        self.assertEqual(q["options"],{"seed":5001,"temperature":0.2,"top_p":0.9,"num_ctx":8192,"num_predict":128})
        self.assertEqual(c["options"]["num_predict"],2048)
        self.assertEqual(q["format"],"json")
        self.assertIs(q["think"],False)

    def test_frozen_plan_has_three_seeds_and_390_calls(self):
        query_calls=3*4*6*5
        consolidation_calls=3*(6+3+1)
        self.assertEqual(tuple(candidate.SEEDS),(5001,5002,5003))
        self.assertEqual(query_calls,360)
        self.assertEqual(consolidation_calls,30)
        self.assertEqual(query_calls+consolidation_calls,390)
        self.assertEqual([q["id"] for q in self.queries["queries"]],
                         ["q_common_save","q_rare_exception","q_conflict","q_history_delta","q_heldout_conjunction"])

    def test_transition_auditor_accepts_exact_faithful_memory(self):
        memory={"claims":[
            {"id":"ep01","kind":"verified_pattern","key":"exact_effect","value":"draft_saved","source_ids":["src-01"]},
            {"id":"ep02","kind":"verified_pattern","key":"exact_effect","value":"draft_saved","source_ids":["src-02"]},
            {"id":"ep03","kind":"forbidden_effect_exception","key":"effects","value":"effect=no_external_effect; forbidden=publish","source_ids":["src-03"]},
            {"id":"ep04","kind":"fact_observation","key":"revision-r7-mode","value":"draft","source_ids":["src-04"]},
            {"id":"ep05","kind":"fact_observation","key":"revision-r7-mode","value":"published","source_ids":["src-05"]},
            {"id":"ep06","kind":"history_delta","key":"revision-r8-mode","value":"draft->published","source_ids":["src-06-baseline","src-06-current"]},
            {"id":"conflict:revision-r7-mode","kind":"conflict","key":"revision-r7-mode","value":"UNKNOWN","source_ids":["src-04","src-05"]},
        ]}
        self.assertEqual(auditor.validate_transition(memory,self.model["episodes"],6,"test"),[])

    def test_transition_auditor_rejects_missing_conflict_and_flattened_history(self):
        memory={"claims":[
            {"id":"ep01","kind":"verified_pattern","key":"exact_effect","value":"draft_saved","source_ids":["src-01"]},
            {"id":"ep02","kind":"verified_pattern","key":"exact_effect","value":"draft_saved","source_ids":["src-02"]},
            {"id":"ep03","kind":"forbidden_effect_exception","key":"effects","value":"effect=no_external_effect; forbidden=publish","source_ids":["src-03"]},
            {"id":"ep04","kind":"fact_observation","key":"revision-r7-mode","value":"draft","source_ids":["src-04"]},
            {"id":"ep05","kind":"fact_observation","key":"revision-r7-mode","value":"published","source_ids":["src-05"]},
            {"id":"ep06","kind":"history_delta","key":"revision-r8-mode","value":"published","source_ids":["src-06-baseline","src-06-current"]},
        ]}
        errors=auditor.validate_transition(memory,self.model["episodes"],6,"test")
        self.assertTrue(any("conflict" in error for error in errors))
        self.assertTrue(any("ep06" in error for error in errors))

    def test_consolidation_template_has_no_fixture_specific_future_literals(self):
        template=self.prompts["consolidation_template"].lower()
        for literal in ("ep01","ep02","ep03","ep04","ep05","ep06","src-01","src-02","src-03","src-04","src-05","src-06","revision-r7-mode","revision-r8-mode","published","draft->published"):
            self.assertNotIn(literal,template)

    def test_prompt_maps_general_episode_kinds_to_allowed_claim_kinds(self):
        template=self.prompts["consolidation_template"]
        for mapping in ("Map common_success to one claim", "kind=verified_pattern", "Map rare_exception to one claim", "kind=forbidden_effect_exception", "Map fact_observation to one claim", "Map history_pair to one claim"):
            self.assertIn(mapping,template)

    def test_prompt_has_context_scoped_conflict_and_prior_claim_rules(self):
        template=self.prompts["consolidation_template"]
        self.assertIn("Copy every prior-memory claim unchanged",template)
        self.assertIn("Only fact_observation claims can form a conflict",template)
        self.assertIn("same subject/applicability context",template)
        self.assertIn("version and the paired field name",template)

    def test_prompt_specifies_one_canonical_claim_per_episode_kind(self):
        template=self.prompts["consolidation_template"]
        self.assertIn("Create exactly one canonical episode claim",template)
        self.assertIn("Do not turn metadata into extra claims",template)
        self.assertIn("Copy every prior-memory claim unchanged",template)
        self.assertIn("Different action/effect claims are not conflicts",template)
        self.assertIn("key formed by joining version and the paired field name",template)

    def test_episode_values_match_byte_copied_t0_source(self):
        source=json.loads((self.pkg/"source_t0_model.json").read_text())
        self.assertEqual(self.model["episodes"],source["episodes"])

    def test_mock_run_raw_rows_and_independent_reconstruction(self):
        def fake_post(_url,payload):
            if "New episodes: " in payload["prompt"]:
                current_text=payload["prompt"].split("New episodes: ",1)[1].split(" Previous memory:",1)[0]
                prior_text=payload["prompt"].split(" Previous memory:",1)[1]
                current=json.loads(current_text); prior=json.loads(prior_text)
                by_id={claim["id"]:claim for claim in prior["claims"]}
                for e in current:
                    if e["id"] in ("ep01","ep02"):
                        claim={"id":e["id"],"kind":"verified_pattern","key":"exact_effect","value":"draft_saved","source_ids":e["source_ids"]}
                    elif e["id"]=="ep03":
                        claim={"id":e["id"],"kind":"forbidden_effect_exception","key":"effects","value":"effect=no_external_effect; forbidden=publish","source_ids":e["source_ids"]}
                    elif e["id"] in ("ep04","ep05"):
                        claim={"id":e["id"],"kind":"fact_observation","key":"revision-r7-mode","value":e["value"],"source_ids":e["source_ids"]}
                    else:
                        claim={"id":e["id"],"kind":"history_delta","key":"revision-r8-mode","value":"draft->published","source_ids":[e["baseline"]["source_id"],e["current"]["source_id"]]}
                    by_id[claim["id"]]=claim
                if "ep04" in by_id and "ep05" in by_id:
                    by_id["conflict:revision-r7-mode"]={"id":"conflict:revision-r7-mode","kind":"conflict","key":"revision-r7-mode","value":"UNKNOWN","source_ids":["src-04","src-05"]}
                response={"claims":list(by_id.values())}
            else:
                response={"classification":"UNKNOWN","answer":None,"source_ids":[]}
            return {"model":"qwen3:8b","response":json.dumps(response),"prompt_eval_count":10,"eval_count":5,"total_duration":1000}
        with tempfile.TemporaryDirectory() as td:
            raw=Path(td)/"raw.jsonl"
            calls = {"n": 0}
            def fake_running(_base):
                calls["n"] += 1
                if calls["n"] == 2: return None, None, "UNLOADED"
                return "test-digest",123,"qwen3:8b"
            with patch.object(candidate,"load_model_tag",return_value=("test-digest",123)), patch.object(candidate,"load_running_model",side_effect=fake_running), patch.object(candidate,"post_json",side_effect=fake_post):
                count=candidate.run(self.model,self.prompts,self.queries,raw,"http://127.0.0.1:11435","test-digest")
            self.assertEqual(count,390)
            result=auditor.audit(raw,self.queries,self.model["episodes"],"test-digest")
            self.assertEqual(result["rows"],390)
            self.assertEqual(result["status"],"PASS_METHOD")
            self.assertEqual(result["errors"],[])
            self.assertLess(result["accuracies"]["5001/episodic_only"],1.0)


if __name__ == "__main__": unittest.main()
