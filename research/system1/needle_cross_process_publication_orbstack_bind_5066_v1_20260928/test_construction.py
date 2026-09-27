"""Fast construction checks; these never launch the formal runner."""
from __future__ import annotations

import base64
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import audit
import protocol
import runner

HERE = Path(__file__).resolve().parent
SEED = HERE.parents[2] / "research/needle_role_skill_reload_3780_v1/formal/seed-3788/builder/skill.json"


class ConstructionTests(unittest.TestCase):
    def test_seed_and_candidate_are_exact_and_valid(self):
        raw = SEED.read_bytes()
        seed = json.loads(raw)
        self.assertEqual(hashlib.sha256(raw).hexdigest(), protocol.SEED_SHA256)
        self.assertTrue(protocol.valid(seed))
        candidate = protocol.successor(seed)
        self.assertTrue(protocol.valid(candidate))
        self.assertEqual(candidate["generation"], protocol.NEW)
        for key in seed["tensors"]:
            self.assertEqual(seed["tensors"][key], candidate["tensors"][key])

    def test_schedule_denominators(self):
        self.assertEqual(len(protocol.PHASES), 7)
        self.assertEqual(len(protocol.UNSAFE_PHASES), 7)
        self.assertEqual(len(protocol.PHASES) * 4 * 2, 56)
        self.assertEqual(7 * 4, 28)

    def test_auditor_rejects_malformed_input(self):
        self.assertTrue(audit.audit(None, None))
        self.assertTrue(audit.audit({}, {}))

    def test_independent_auditor_reconstructs_raw_package_bytes(self):
        seed = json.loads(SEED.read_bytes())
        raw = protocol.canonical_bytes(protocol.successor(seed))
        value = json.loads(raw)
        row = {"raw_b64":base64.b64encode(raw).decode(),"bytes":len(raw),
               "raw_sha256":hashlib.sha256(raw).hexdigest(),"parse_ok":True,
               "valid":True,"generation":value["generation"],
               "embedded_digest":value["payload_sha256"]}
        rebuilt = audit.reconstructed(row)
        self.assertIsNotNone(rebuilt)
        self.assertEqual(rebuilt["raw"], raw)
        row["raw_sha256"] = "0" * 64
        self.assertIsNone(audit.reconstructed(row))
        array_raw = b"[]"
        scalar_row = {"raw_b64":base64.b64encode(array_raw).decode(),"bytes":2,
                      "raw_sha256":hashlib.sha256(array_raw).hexdigest(),"parse_ok":True,
                      "valid":False,"generation":None,"embedded_digest":None}
        self.assertIsNone(audit.reconstructed(scalar_row))

    def test_independent_candidate_derivation_matches_all_frozen_phases(self):
        seed=json.loads(SEED.read_bytes())
        for generation in range(protocol.NEW,protocol.NEW+7):
            self.assertEqual(audit.expected_candidate(seed,generation),
                             protocol.canonical_bytes(protocol.successor(seed,generation)))

    def test_rehashed_wrong_lineage_is_not_frozen_candidate(self):
        seed=json.loads(SEED.read_bytes());candidate=protocol.successor(seed,protocol.NEW)
        wrong=copy.deepcopy(candidate);wrong["provenance"]["allocation"]="unregistered-allocation"
        wrong["payload_sha256"]=protocol.digest(wrong)
        raw=protocol.canonical_bytes(wrong);parsed=json.loads(raw)
        row={"raw_b64":base64.b64encode(raw).decode(),"bytes":len(raw),
             "raw_sha256":hashlib.sha256(raw).hexdigest(),"parse_ok":True,"valid":True,
             "generation":parsed["generation"],"embedded_digest":parsed["payload_sha256"]}
        self.assertTrue(audit.reconstructed(row)["valid"])
        self.assertFalse(audit.exact_raw_matches(row,audit.expected_candidate(seed,protocol.NEW)))

    def test_wrong_lineage_in_formal_rows_is_rejected_by_raw_auditor(self):
        seed=json.loads(SEED.read_bytes())
        correct=protocol.successor(seed,protocol.NEW)
        wrong=copy.deepcopy(correct);wrong["provenance"]["seed"]=9999
        wrong["payload_sha256"]=protocol.digest(wrong)
        raw_bytes=protocol.canonical_bytes(wrong);obj=json.loads(raw_bytes)
        observation={"raw_b64":base64.b64encode(raw_bytes).decode(),"bytes":len(raw_bytes),
                     "raw_sha256":hashlib.sha256(raw_bytes).hexdigest(),"parse_ok":True,"valid":True,
                     "generation":obj["generation"],"embedded_digest":obj["payload_sha256"]}
        control=audit.expected_candidate(seed,protocol.NEW)
        self.assertNotEqual(raw_bytes,control)
        self.assertEqual(obj["payload_sha256"],protocol.digest(wrong))
        self.assertFalse(audit.exact_raw_matches(observation,control))

    def test_real_admission_path_publishes_next_and_preserves_on_invalid_or_stale(self):
        seed=json.loads(SEED.read_bytes())
        first=protocol.successor(seed,3789);second=protocol.successor(seed,3790)
        with tempfile.TemporaryDirectory() as tmp:
            active=Path(tmp)/"ACTIVE.json";temporary=Path(tmp)/"candidate.tmp"
            active.write_bytes(SEED.read_bytes())
            published=runner.try_publish(active,temporary,3788,protocol.canonical_bytes(first))
            self.assertEqual(published["disposition"],"PUBLISHED")
            active_after=hashlib.sha256(active.read_bytes()).hexdigest()
            bad=dict(second);bad["payload_sha256"]="0"*64
            invalid=runner.try_publish(active,temporary,3789,protocol.canonical_bytes(bad))
            stale=runner.try_publish(active,temporary,3788,protocol.canonical_bytes(second))
            self.assertEqual(invalid["disposition"],"YIELD_INVALID_CANDIDATE")
            self.assertEqual(stale["disposition"],"YIELD_STALE_GENERATION")
            self.assertEqual(hashlib.sha256(active.read_bytes()).hexdigest(),active_after)
            self.assertFalse(temporary.exists())


if __name__ == "__main__":
    unittest.main()
