import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import candidate
import auditor
import preflight


class ConstructionTests(unittest.TestCase):
    def setUp(self):
        self.pkg = Path(__file__).parent
        self.model = json.loads((self.pkg/"episode_ledger.json").read_text())
        self.prompts = json.loads((self.pkg/"prompts.json").read_text())
        self.queries = json.loads((self.pkg/"queries.json").read_text())

    def test_private_preflight_checks_all_manifest_blobs(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            manifest=root/"manifests/registry.ollama.ai/library/qwen3/8b"
            manifest.parent.mkdir(parents=True)
            model_blob=b"model-layer"
            digest=__import__("hashlib").sha256(model_blob).hexdigest()
            tag_blob=preflight.EXPECTED.encode()
            (root/"blobs").mkdir()
            (root/"blobs"/f"sha256-{digest}").write_bytes(model_blob)
            (root/"blobs"/f"sha256-{preflight.EXPECTED}").write_bytes(tag_blob)
            manifest.write_text(json.dumps({"layers":[
                {"mediaType":"application/vnd.ollama.image.model","digest":"sha256:"+digest,"size":len(model_blob)},
                {"mediaType":"application/vnd.docker.distribution.manifest.v2+json","digest":"sha256:"+preflight.EXPECTED,"size":len(tag_blob)}
            ]}))
            result=preflight.check({"models":[{"name":"qwen3:8b","digest":preflight.EXPECTED,"size":len(model_blob)}]},root)
            self.assertTrue(result["all_manifest_blobs_present_and_size_matched"])
            self.assertEqual(len(result["checked_layers"]),2)

    def test_private_preflight_rejects_wrong_tag_digest(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(RuntimeError,"digest"):
                preflight.check({"models":[{"name":"qwen3:8b","digest":"wrong"}]},td)

    def test_query_and_consolidation_options_are_fixed_and_seeded(self):
        q = candidate.request_body(self.model,self.prompts,{"kind":"query","question":"q","evidence":{}},5201,128)
        c = candidate.request_body(self.model,self.prompts,{"kind":"consolidate","episodes":[],"memory":{"claims":[]}},5201,2048)
        self.assertEqual(q["options"],{"seed":5201,"temperature":0.2,"top_p":0.9,"num_ctx":8192,"num_predict":128})
        self.assertEqual(c["options"]["num_predict"],2048)
        self.assertEqual(q["format"],"json")
        self.assertIs(q["think"],False)

    def test_frozen_plan_has_three_seeds_and_390_calls(self):
        query_calls=3*4*6*5
        consolidation_calls=3*(6+3+1)
        self.assertEqual(tuple(candidate.SEEDS),(5201,5202,5203))
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
        for mapping in ("common_success -> id=<episode.id>", "kind=verified_pattern", "rare_exception -> id=<episode.id>", "kind=forbidden_effect_exception", "fact_observation -> id=<episode.id>", "history_pair -> let <field>"):
            self.assertIn(mapping,template)

    def test_prompt_has_context_scoped_conflict_and_prior_claim_rules(self):
        template=self.prompts["consolidation_template"]
        self.assertIn("Copy every prior claim exactly once and unchanged",template)
        self.assertIn("Only fact_observation claims can conflict",template)
        self.assertIn("subject/applicability scope match",template)
        self.assertIn('key=<version> + "-" + <field>',template)

    def test_prompt_specifies_one_canonical_claim_per_episode_kind(self):
        template=self.prompts["consolidation_template"]
        self.assertIn("For each input episode create exactly one claim",template)
        self.assertIn("Ignore all fields not named by the matching mapping",template)
        self.assertIn("Copy every prior claim exactly once and unchanged",template)
        self.assertIn("Never conflict action/effect claims",template)
        self.assertIn('key=<version> + "-" + <field>',template)

    def test_episode_values_match_byte_copied_t0_source(self):
        source=json.loads((self.pkg/"source_t0_model.json").read_text())
        self.assertEqual(self.model["episodes"],source["episodes"])
        self.assertEqual(self.model["allocation"],"GUI-MEMORY-CONSOLIDATION-SCHEDULE-8406-T1-A12-PRIVATE-PREFLIGHT-20261008")

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
            self.assertLess(result["accuracies"]["5201/episodic_only"],1.0)


    def test_prompt_mapping_examples_are_symbolic_and_explicit(self):
        template=self.prompts["consolidation_template"]
        for text in ("kind=forbidden_effect_exception", "key=<episode.fact_key VALUE>", "key=<version> + \"-\" + <field>", "never output the literal field label \"fact_key\"", "Copy every prior claim exactly once"):
            self.assertIn(text,template)
        for forbidden in ("ep01", "ep02", "ep03", "ep04", "ep05", "ep06", "src-01", "src-02", "src-03", "src-04", "src-05", "src-06", "revision-r7-mode", "revision-r8-mode", "draft->published"):
            self.assertNotIn(forbidden,template)

    def test_prompt_has_frozen_transition_rules(self):
        template=self.prompts["consolidation_template"]
        for text in ("same scope", "Only fact_observation claims can conflict", "Never conflict action/effect claims", "Never anticipate unseen evidence", "exact union of both source_ids"):
            self.assertIn(text,template)

if __name__ == "__main__": unittest.main()
