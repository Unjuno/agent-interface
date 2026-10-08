import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import auditor
import candidate
import preflight


class A19ConstructionTests(unittest.TestCase):
    def setUp(self):
        self.package = Path(__file__).parent
        self.ledger = json.loads((self.package/"episode_ledger.json").read_text())
        self.queries = json.loads((self.package/"queries.json").read_text())
        self.prompts = json.loads((self.package/"prompts.json").read_text())

    def test_second_corpus_has_six_ordered_episodes_and_unique_source_atoms(self):
        episodes = self.ledger["episodes"]
        self.assertEqual([episode["id"] for episode in episodes], [f"ep{i:02d}" for i in range(1, 7)])
        atoms = [fact for episode in episodes for fact in episode["facts"]]
        self.assertGreater(len(atoms), len(episodes))
        ids = [fact["id"] for fact in atoms]
        source_ids = [source for fact in atoms for source in fact["source_ids"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(source_ids), len(set(source_ids)))
        for fact in atoms:
            self.assertEqual(set(fact["scope"]), {"app", "mode", "surface"})
            self.assertTrue(all(fact["scope"].values()))

    def test_each_family_has_two_distinct_query_items_batched_in_fixed_order(self):
        self.assertEqual(self.queries["families"], ["common", "rare_exception", "conflict", "history", "heldout"])
        ids = [query["id"] for query in self.queries["queries"]]
        self.assertEqual(len(ids), 10)
        self.assertEqual(len(set(ids)), 10)
        for family in self.queries["families"]:
            group = [query for query in self.queries["queries"] if query["family"] == family]
            self.assertEqual(len(group), 2)
            self.assertNotEqual(group[0]["question"], group[1]["question"])

    def test_schedule_allocation_is_390_model_calls_and_720_answer_items(self):
        query_calls = len(candidate.SEEDS)*len(candidate.ARMS)*len(candidate.PREFIXES)*len(self.queries["families"])
        update_calls = len(candidate.SEEDS)*(6+3+1)
        answer_items = query_calls*2
        self.assertEqual((query_calls, update_calls, query_calls+update_calls, answer_items), (360, 30, 390, 720))

    def test_schema_requires_full_scope_and_has_no_open_scope_object(self):
        scope = candidate.CLAIM_SCHEMA["properties"]["scope"]
        self.assertEqual(scope["required"], ["app", "mode", "surface"])
        self.assertIs(scope["additionalProperties"], False)
        self.assertEqual(candidate.CONSOLIDATION_SCHEMA, auditor.CONSOLIDATION_SCHEMA)
        self.assertEqual(candidate.ANSWER_SCHEMA, auditor.ANSWER_SCHEMA)

    def test_independent_oracle_uses_only_visible_evidence(self):
        query = next(item for item in self.queries["queries"] if item["id"] == "q_common_save")
        ledger_prefix = {"episodes": self.ledger["episodes"][:1]}
        self.assertEqual(auditor.answer_from_visible_evidence(query, ledger_prefix), {
            "query_id": "q_common_save", "classification": "SUPPORTED", "answer": "draft_saved", "source_ids": ["src-01"]})
        # Hidden fixture truth must not leak into a summary-arm answerability score.
        self.assertEqual(auditor.answer_from_visible_evidence(query, {"claims": []}), {
            "query_id": "q_common_save", "classification": "UNKNOWN", "answer": None, "source_ids": []})

    def test_scope_loss_is_rejected_even_when_claim_value_and_source_are_correct(self):
        expected = auditor.reconstructed_memory(self.ledger["episodes"][:1])
        self.assertEqual(auditor.check_scope_contract(expected, "control"), [])
        corrupted = json.loads(json.dumps(expected))
        del corrupted["claims"][0]["scope"]["mode"]
        errors = auditor.check_scope_contract(corrupted, "mutation")
        self.assertTrue(any("incomplete applicability scope" in error for error in errors))
        self.assertNotEqual(corrupted, auditor.reconstructed_memory(self.ledger["episodes"][:1]))

    def test_conflict_requires_both_matching_observations_and_never_arrives_early(self):
        first = auditor.reconstructed_memory(self.ledger["episodes"][:4])
        complete = auditor.reconstructed_memory(self.ledger["episodes"][:5])
        self.assertFalse(any(claim["kind"] == "conflict" for claim in first["claims"]))
        conflict = [claim for claim in complete["claims"] if claim["kind"] == "conflict"]
        self.assertEqual(len(conflict), 2)
        self.assertEqual({claim["id"] for claim in conflict}, {"conflict:document:rev-q4:mode", "conflict:document:rev-q4:visibility"})
        self.assertEqual({tuple(claim["source_ids"]) for claim in conflict}, {("src-04", "src-05")})

    def test_scope_mismatch_returns_unknown_even_when_action_and_field_match(self):
        query = next(item for item in self.queries["queries"] if item["id"] == "q_heldout_publish_save")
        evidence = {"episodes": self.ledger["episodes"][:1]}
        self.assertEqual(auditor.answer_from_visible_evidence(query, evidence), {
            "query_id":"q_heldout_publish_save","classification":"UNKNOWN","answer":None,"source_ids":[]})

    def test_heldout_conjunctions_stay_unknown_under_the_exact_scope_oracle(self):
        full = {"episodes": self.ledger["episodes"]}
        for query in self.queries["queries"]:
            if query["family"] == "heldout":
                self.assertEqual(auditor.answer_from_visible_evidence(query, full)["classification"], "UNKNOWN")

    def test_decoder_options_are_frozen_for_two_question_batches(self):
        query_group = [query for query in self.queries["queries"] if query["family"] == "common"]
        query_request = candidate.request_body(self.prompts, {"kind":"query", "queries":query_group, "evidence":{"claims":[]}}, 5801)
        consolidation_request = candidate.request_body(self.prompts, {"kind":"consolidate", "episodes":[], "memory":{"claims":[]}}, 5801)
        self.assertEqual(query_request["options"], {"seed":5801,"temperature":0.2,"top_p":0.9,"num_ctx":8192,"num_predict":512})
        self.assertEqual(consolidation_request["options"]["num_predict"], 4096)
        self.assertEqual(query_request["format"], candidate.ANSWER_SCHEMA)
        self.assertEqual(consolidation_request["format"], candidate.CONSOLIDATION_SCHEMA)

    def test_preflight_checks_existing_manifest_blobs_without_download(self):
        import hashlib
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            model_blob, config_blob = b"model-layer", b"config-layer"
            model_digest, config_digest = hashlib.sha256(model_blob).hexdigest(), hashlib.sha256(config_blob).hexdigest()
            (root/"blobs").mkdir()
            (root/"blobs"/f"sha256-{model_digest}").write_bytes(model_blob)
            (root/"blobs"/f"sha256-{config_digest}").write_bytes(config_blob)
            manifest = root/"manifests/registry.ollama.ai/library/qwen3/14b"
            manifest.parent.mkdir(parents=True)
            manifest.write_text(json.dumps({"layers":[
                {"digest":"sha256:"+model_digest,"size":len(model_blob)},
                {"digest":"sha256:"+config_digest,"size":len(config_blob)}]}))
            result = preflight.check_store(root)
            self.assertTrue(result["all_manifest_blobs_present_and_size_matched"])
            self.assertEqual(len(result["checked_layers"]), 2)
            with self.assertRaisesRegex(RuntimeError, "digest"):
                preflight.check_tag({"models":[{"name":"qwen3:14b","digest":"wrong"}]})

    def test_candidate_stops_before_raw_or_inference_if_model_is_preloaded(self):
        with tempfile.TemporaryDirectory() as directory:
            raw = Path(directory)/"raw.jsonl"
            with patch.object(candidate, "load_model_tag", return_value=(candidate.EXPECTED_DIGEST, 123)), \
                 patch.object(candidate, "load_running_model", return_value=(candidate.EXPECTED_DIGEST, 123, candidate.MODEL)), \
                 patch.object(candidate, "post_json") as post:
                with self.assertRaisesRegex(RuntimeError, "unloaded"):
                    candidate.run(self.ledger, self.queries, self.prompts, raw)
                post.assert_not_called()
            self.assertFalse(raw.exists())

    def test_mock_candidate_and_raw_only_auditor_pass_once_without_retry(self):
        raw_rows = {"count": 0}
        running = {"loaded": False}

        def fake_running(_url):
            if not running["loaded"]:
                return None, None, "UNLOADED"
            return candidate.EXPECTED_DIGEST, 123, candidate.MODEL

        def model_consolidation(prompt):
            text = prompt.split("New episodes (JSON): ", 1)[1]
            batch_text, prior_text = text.split("\nPrior evidence memory (JSON): ", 1)
            episodes = json.loads(batch_text)
            prior = json.loads(prior_text)
            claims = {claim["id"]: claim for claim in prior["claims"]}
            for episode in episodes:
                for fact in episode["facts"]:
                    claims[fact["id"]] = fact
            facts = list(claims.values())
            observations = {}
            for fact in facts:
                if fact["kind"] != "fact_observation":
                    continue
                for field, value in fact["fields"].items():
                    key = (fact["subject"], auditor.canonical(fact["scope"]), field)
                    observations.setdefault(key, []).append((fact, value))
            for (subject, scope_text, field), entries in observations.items():
                if len({value for _, value in entries}) > 1:
                    claims[f"conflict:{subject}:{field}"] = {
                        "id": f"conflict:{subject}:{field}", "kind":"conflict", "subject":subject,
                        "scope":json.loads(scope_text), "fields":{field:"UNKNOWN"},
                        "source_ids":sorted({source for fact, _ in entries for source in fact["source_ids"]})}
            return {"claims": sorted(claims.values(), key=lambda claim: claim["id"])}

        def fake_answer(query, evidence):
            matches = []
            for fact in auditor.visible_facts(evidence):
                if fact.get("kind") == "conflict" or fact.get("subject") != query["subject"] or fact.get("scope") != query["scope"]:
                    continue
                if query["field"] in fact.get("fields", {}):
                    matches.append((fact, fact["fields"][query["field"]]))
            if not matches:
                return {"query_id":query["id"],"classification":"UNKNOWN","answer":None,"source_ids":[]}
            values = {value for _, value in matches}
            if len(values) > 1 and {fact["kind"] for fact, _ in matches} == {"fact_observation"}:
                classification, answer = "CONFLICT", None
            elif len(values) > 1:
                classification, answer = "UNKNOWN", None
                matches = []
            else:
                classification = "FORBIDDEN" if query["field"] == "forbidden_effect" else "SUPPORTED"
                answer = next(iter(values))
            sources = sorted({source for fact, _ in matches for source in fact["source_ids"]})
            return {"query_id":query["id"],"classification":classification,"answer":answer,"source_ids":sources}

        def fake_post(_url, payload):
            raw_rows["count"] += 1
            prompt = payload["prompt"]
            if "New episodes (JSON): " in prompt:
                response = model_consolidation(prompt)
            else:
                query_text = prompt.split("Queries (JSON): ", 1)[1]
                queries_text, evidence_text = query_text.split("\nVisible evidence (JSON): ", 1)
                qs, evidence = json.loads(queries_text), json.loads(evidence_text)
                response = {"answers":[fake_answer(query, evidence) for query in qs]}
            running["loaded"] = True
            return {"model":candidate.MODEL,"response":json.dumps(response),"prompt_eval_count":20,"eval_count":10,"total_duration":1000}

        with tempfile.TemporaryDirectory() as directory:
            raw = Path(directory)/"raw.jsonl"
            with patch.object(candidate, "load_model_tag", return_value=(candidate.EXPECTED_DIGEST, 123)), \
                 patch.object(candidate, "load_running_model", side_effect=fake_running), \
                 patch.object(candidate, "post_json", side_effect=fake_post):
                count = candidate.run(self.ledger, self.queries, self.prompts, raw)
                result = auditor.audit(raw, self.ledger, self.queries, self.prompts)
                running["loaded"] = False
                with self.assertRaises(FileExistsError):
                    candidate.run(self.ledger, self.queries, self.prompts, raw)
            self.assertEqual(count, 390)
            self.assertEqual(raw_rows["count"], 390)
            self.assertEqual(result["status"], "PASS_METHOD")
            self.assertEqual(result["decision"], "NO_10PP_CONTRAST_OBSERVED_SCOPED")
            self.assertTrue(all(value == 1.0 for value in result["accuracy_by_seed_arm"].values()))
            self.assertEqual(result["errors"], [])
            self.assertEqual(result["query_answer_items"], 720)
            mutated = Path(directory)/"scope-dropped.jsonl"
            rows = [json.loads(line) for line in raw.read_text().splitlines()]
            transition = next(row for row in rows if row["type"] == "consolidation")
            claims = json.loads(transition["response"]["response"])
            del claims["claims"][0]["scope"]["mode"]
            transition["response"]["response"] = json.dumps(claims)
            mutated.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows))
            rejected = auditor.audit(mutated, self.ledger, self.queries, self.prompts)
            self.assertEqual(rejected["status"], "FAIL_METHOD")
            self.assertTrue(any("scope" in error or "transition mismatch" in error for error in rejected["errors"]))
            prompt_mutation = Path(directory)/"prompt-mutated.jsonl"
            query_row = next(row for row in rows if row["type"] == "query")
            query_row["request"]["system"] = "modified system prompt"
            prompt_mutation.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows))
            rejected_prompt = auditor.audit(prompt_mutation, self.ledger, self.queries, self.prompts)
            self.assertEqual(rejected_prompt["status"], "FAIL_METHOD")
            self.assertTrue(any("system prompt drift" in error for error in rejected_prompt["errors"]))
            wrong_answer = Path(directory)/"wrong-answer.jsonl"
            wrong_rows = [json.loads(line) for line in raw.read_text().splitlines()]
            query_row = next(row for row in wrong_rows if row["type"] == "query")
            answer_payload = json.loads(query_row["response"]["response"])
            answer_payload["answers"][0]["answer"] = "mutated-answer"
            query_row["response"]["response"] = json.dumps(answer_payload)
            wrong_answer.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in wrong_rows))
            scored = auditor.audit(wrong_answer, self.ledger, self.queries, self.prompts)
            self.assertEqual(scored["status"], "PASS_METHOD")
            self.assertEqual(sum(cost["answer_errors"] for cost in scored["costs"].values()), 1)
            threshold_contrast = Path(directory)/"threshold-contrast.jsonl"
            threshold_rows = [json.loads(line) for line in raw.read_text().splitlines()]
            for seed in auditor.SEEDS:
                arm_rows = [row for row in threshold_rows if row["type"] == "query" and row["seed"] == seed and row["arm"] == "per_episode"]
                self.assertEqual(len(arm_rows), 30)
                for row in arm_rows[:6]:
                    answer_payload = json.loads(row["response"]["response"])
                    answer_payload["answers"][0]["answer"] = "mutated-answer"
                    row["response"]["response"] = json.dumps(answer_payload)
            threshold_contrast.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in threshold_rows))
            observed = auditor.audit(threshold_contrast, self.ledger, self.queries, self.prompts)
            self.assertEqual(observed["status"], "PASS_METHOD")
            self.assertEqual(observed["decision"], "OBSERVED_CADENCE_CONTRAST_SCOPED")
            self.assertEqual(observed["paired_accuracy_differences"]["5801:episodic_only-per_episode"], 0.1)
            self.assertEqual(observed["paired_accuracy_differences"]["5802:episodic_only-per_episode"], 0.1)
            self.assertEqual(observed["paired_accuracy_differences"]["5803:episodic_only-per_episode"], 0.1)
            invalid_response = Path(directory)/"invalid-response.jsonl"
            invalid_rows = [json.loads(line) for line in raw.read_text().splitlines()]
            query_row = next(row for row in invalid_rows if row["type"] == "query")
            answer_payload = json.loads(query_row["response"]["response"])
            answer_payload["answers"][0]["classification"] = "INVALID"
            query_row["response"]["response"] = json.dumps(answer_payload)
            invalid_response.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in invalid_rows))
            rejected_shape = auditor.audit(invalid_response, self.ledger, self.queries, self.prompts)
            self.assertEqual(rejected_shape["status"], "FAIL_METHOD")
            self.assertTrue(any("answer response schema invalid" in error for error in rejected_shape["errors"]))


if __name__ == "__main__":
    unittest.main()
