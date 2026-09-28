"""Fast construction checks; these never launch the formal runner."""
from __future__ import annotations

import base64
import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import audit
import formal
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

    def test_formal_launch_requires_latest_exact_owner_release_on_frozen_main(self):
        allocation=protocol.ALLOCATION
        main_sha="a"*40
        marker=formal.release_marker(5074,allocation,main_sha)
        comments=[{"id":10,"created_at":"2026-09-28T10:00:00Z","user":{"login":"Unjuno"},"body":marker}]
        accepted=formal.verify_slot_release(comments,10,5074,allocation,main_sha)
        self.assertEqual(accepted["comment_id"],10)
        queue_marker=formal.release_marker(5085,allocation,main_sha)
        queue_comments=[{"id":20,"created_at":"2026-09-28T10:00:00Z","user":{"login":"Unjuno"},"body":queue_marker}]
        self.assertEqual(formal.verify_slot_release(queue_comments,20,5085,allocation,main_sha)["issue"],5085)
        for bad_comments,bad_id in (
            (comments,11),
            ([{"id":10,"created_at":"2026-09-28T10:00:00Z","user":{"login":"Unjuno"},"body":"Quoted request: `"+marker+"`"}],10),
            ([*comments,{"id":12,"created_at":"2026-09-28T10:01:00Z","user":{"login":"Unjuno"},"body":"hold"}],10),
            ([{"id":10,"created_at":"2026-09-28T10:00:00Z","user":{"login":"someone-else"},"body":marker}],10),
        ):
            with self.assertRaises(RuntimeError):
                formal.verify_slot_release(bad_comments,bad_id,5074,allocation,main_sha)
        with self.assertRaises(RuntimeError):
            formal.verify_slot_release(comments,10,5074,allocation,"b"*40)
        with self.assertRaises(RuntimeError):
            formal.verify_slot_release(comments,10,5085,allocation,main_sha)

    def test_raw_receipt_contract_accepts_exact_platform_and_experiment_relative_sources(self):
        freeze=json.loads((HERE/"FREEZE.json").read_bytes())
        source_hashes={name:hashlib.sha256((HERE/name).read_bytes()).hexdigest()
                       for name in ("PLAN.md","protocol.py","runner.py","audit.py","formal.py","test_construction.py")}
        source_blobs={name:audit.blob_id((HERE/name).read_bytes()) for name in source_hashes}
        main_sha="4"*40
        commit="1"*40
        output_mount="/tmp/needle-publication-5134-fixture"
        mounts=[{"Type":"bind","Source":"/repo","Destination":"/src","RW":False},
                {"Type":"bind","Source":output_mount,"Destination":"/out","RW":True}]
        audit_input_mount=output_mount+"/audit-input"
        audit_output_mount=output_mount+"/audit-output"
        auditor_mounts=[{"Type":"bind","Source":"/repo","Destination":"/src","RW":False},
                        {"Type":"bind","Source":audit_input_mount,"Destination":"/in","RW":False},
                        {"Type":"bind","Source":audit_output_mount,"Destination":"/out","RW":True}]
        env={"OBSTAC_SOURCE_COMMIT":commit,"OBSTAC_IMAGE_ID":protocol.IMAGE_ID,
             "OBSTAC_FREEZE_SHA256":"2"*64,"OBSTAC_CONSTRUCTION":"0"}
        receipt={"source_commit":commit,"live_main_sha":main_sha,"source_tree_sha":"3"*40,
                 "freeze_sha256":env["OBSTAC_FREEZE_SHA256"],"source_sha256":source_hashes,
                 "source_blob_sha256":source_blobs,"image_id":protocol.IMAGE_ID,"mounts":mounts,
                 "docker_context":"orbstack","image_platform":"linux/arm64","construction":"0",
                 "environment":env,"source_mount":"/repo","output_mount":output_mount,
                 "auditor_mounts":auditor_mounts,"audit_input_mount":audit_input_mount,"audit_output_mount":audit_output_mount,
                 "formal_container_name":"unjuno5134-formal-11111111",
                 "auditor_container_name":"unjuno5134-audit-11111111"}
        receipt["docker_argv"]=audit.expected_docker_argv(receipt,"runner")
        receipt["auditor_docker_argv"]=audit.expected_docker_argv(receipt,"audit")
        raw={"allocation":protocol.ALLOCATION,"issue":5134,"formal_invocations":1,
             "image_id":protocol.IMAGE_ID,"input_sha256":protocol.SEED_SHA256,"input_bytes":15279,
             "input_git_blob":"45b80150dac503f4eb6f3cb5d82f9afa2c587107","platform":"linux/arm64",
             "dispatch_count":0,"authority_granted":False,"source_commit":commit,
                 "live_main_sha":main_sha,"source_tree_sha":receipt["source_tree_sha"],
             "freeze_sha256":receipt["freeze_sha256"],"source_sha256":source_hashes,
             "source_blob_sha256":source_blobs,"mounts":mounts,"construction":"0"}
        with tempfile.TemporaryDirectory() as tmp:
            inp=Path(tmp)
            raw_bytes=json.dumps(raw,sort_keys=True,indent=2).encode()+b"\n"
            receipt_bytes=json.dumps(receipt,sort_keys=True,indent=2).encode()+b"\n"
            (inp/"raw.json").write_bytes(raw_bytes)
            (inp/"invocation_receipt.json").write_bytes(receipt_bytes)
            (inp/"input_manifest.json").write_text(json.dumps({"files":{"raw.json":hashlib.sha256(raw_bytes).hexdigest(),
                "invocation_receipt.json":hashlib.sha256(receipt_bytes).hexdigest()}},sort_keys=True,indent=2)+"\n")
            with patch.dict(os.environ,env,clear=False):
                self.assertEqual(audit.provenance_errors(raw,receipt,HERE,inp),[])
                damaged=copy.deepcopy(raw);damaged["platform"]="linux/amd64"
                self.assertIn("raw_platform_prefix",audit.provenance_errors(damaged,receipt,HERE,inp))
                damaged_receipt=copy.deepcopy(receipt);damaged_receipt["docker_argv"]=[*receipt["docker_argv"][:-1],"/wrong/runner.py"]
                self.assertIn("receipt_docker_argv",audit.provenance_errors(raw,damaged_receipt,HERE,inp))
                damaged_row={"fd_open_ns":1,"replace_start_ns":2,"replace_return_ns":5,"fd_read_start_ns":4,"fd_read_end_ns":6}
                self.assertEqual(audit.fd_read_order_errors(damaged_row,"phase_1"),["fd_partial_order_phase_1"])
                good_row={**damaged_row,"fd_read_start_ns":6,"fd_read_end_ns":7}
                self.assertEqual(audit.fd_read_order_errors(good_row,"phase_1"),[])
                missing_row={**good_row,"fd_read_start_ns":None}
                self.assertEqual(audit.fd_read_order_errors(missing_row,"phase_1"),["fd_timestamps_missing_phase_1"])
                bad_mount=copy.deepcopy(receipt);bad_mount["auditor_mounts"][1]["RW"]=True
                self.assertIn("auditor_mount_/in",audit.provenance_errors(raw,bad_mount,HERE,inp))
                (inp/"input_manifest.json").write_text("{}\n")
                self.assertIn("audit_input_manifest",audit.provenance_errors(raw,receipt,HERE,inp))
                (inp/"input_manifest.json").write_text(json.dumps({"files":{"raw.json":"0"*64}},sort_keys=True)+"\n")
                self.assertIn("audit_input_manifest",audit.provenance_errors(raw,receipt,HERE,inp))

    def test_unsafe_completion_must_follow_and_match_writer_interval(self):
        row={"phase":"phase_1","write_start_ns":10,"partial_start_ns":20,"partial_end_ns":30,
             "write_end_ns":40,"complete_start_ns":41,"complete_end_ns":50}
        interval={"phase":"phase_1","start_ns":10,"end_ns":40}
        self.assertEqual(audit.unsafe_completion_errors(row,interval),[])
        for key,value in (("complete_start_ns",39),("complete_end_ns",40),("write_end_ns",42)):
            damaged=dict(row);damaged[key]=value
            self.assertIn("completion_order",audit.unsafe_completion_errors(damaged,interval))
        wrong_interval={**interval,"phase":"phase_2"}
        self.assertIn("phase",audit.unsafe_completion_errors(row,wrong_interval))
        wrong_interval={**interval,"end_ns":39}
        self.assertIn("interval_binding",audit.unsafe_completion_errors(row,wrong_interval))


if __name__ == "__main__":
    unittest.main()
