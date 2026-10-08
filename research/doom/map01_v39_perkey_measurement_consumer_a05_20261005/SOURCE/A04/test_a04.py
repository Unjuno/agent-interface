from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path

import audit
import candidate

HERE = Path(__file__).resolve().parent
_consumer_spec = importlib.util.spec_from_file_location(
    "consumer_for_a04_tests", HERE / "SOURCE/consumer_a03.py")
consumer_a03 = importlib.util.module_from_spec(_consumer_spec)
_consumer_spec.loader.exec_module(consumer_a03)


class CleanupConsumerCompositionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = json.loads((HERE / "SOURCE/BRIDGE_RAW_A01.json").read_text(encoding="utf-8"))
        cls.a03_oracle = staticmethod(
            audit.load_a03_auditor(HERE / "SOURCE/audit_a03.py"))

    def test_retained_cleanup_projects_into_strict_consumer(self):
        events = candidate.project_cleanup(copy.deepcopy(self.raw))
        result = audit.audit_result(self.raw, {
            "projected_events": events,
            "candidate": consumer_a03.reconstruct(events),
            "status": "PENDING_INDEPENDENT_AUDIT",
            "authority_granted": False,
            "application_effect_observed": False,
            "candidate_invocations": 1,
            "new_os_input": False, "new_gui_or_game": False, "new_model_call": False,
        }, self.a03_oracle)
        self.assertEqual(result["disposition"], "PASS_CLEANUP_CONSUMER_COMPOSITION_SCOPED")
        self.assertEqual(events[1]["id"], events[0]["id"])
        self.assertEqual(events[1]["step"], events[0]["step"])
        self.assertEqual(events[1]["physical_key_measurement"]["actuation_id"],
                         events[0]["physical_key_measurement"]["actuation_id"])
        self.assertFalse(result["authority_granted"])
        self.assertFalse(result["application_effect_observed"])

    def test_candidate_fails_closed_on_cleanup_identity_and_ambiguity(self):
        cases = []
        bad = copy.deepcopy(self.raw)
        bad["owner_cleanup_record"]["per_key_release_measurements"][0]["actuation_id"] = "foreign"
        cases.append(bad)
        bad = copy.deepcopy(self.raw)
        bad["owner_cleanup_record"]["per_key_release_measurements"].append(
            copy.deepcopy(bad["owner_cleanup_record"]["per_key_release_measurements"][0]))
        cases.append(bad)
        for bad in cases:
            with self.subTest(case=len(cases)):
                with self.assertRaises(candidate.ProjectionError):
                    candidate.project_cleanup(bad)

    def test_candidate_rejects_invalid_samples_timing_and_context(self):
        mutations = (
            lambda r: r["owner_cleanup_record"]["per_key_release_measurements"][0]["pre_sample"].update(available=False),
            lambda r: r["owner_cleanup_record"]["per_key_release_measurements"][0]["post_sample"].update(down=True),
            lambda r: r["owner_cleanup_record"]["per_key_release_measurements"][0].update(
                sync_return_ns=r["owner_cleanup_record"]["per_key_release_measurements"][0]["post_sample"]["finished_ns"]+1),
            lambda r: r["bridge_emitted_events"][0].update(step=True),
            lambda r: r["owner_cleanup_record"].update(verified=False),
        )
        for mutate in mutations:
            bad = copy.deepcopy(self.raw)
            mutate(bad)
            with self.subTest(mutation=mutate):
                with self.assertRaises(candidate.ProjectionError):
                    candidate.project_cleanup(bad)

    def test_independent_audit_rejects_candidate_event_or_summary_forgery(self):
        events = candidate.project_cleanup(copy.deepcopy(self.raw))
        consumer = consumer_a03.reconstruct(events)
        result = {
            "projected_events": events, "candidate": consumer,
            "status": "PENDING_INDEPENDENT_AUDIT", "authority_granted": False,
            "application_effect_observed": False, "candidate_invocations": 1,
            "new_os_input": False, "new_gui_or_game": False, "new_model_call": False,
        }
        for mutate in (
            lambda x: x["projected_events"][1].update(step=9),
            lambda x: x["projected_events"][1]["physical_key_measurement"]["adapter_edge"].update(actuation_id="foreign"),
            lambda x: x["candidate"].update(hold_duration_lower_bound_ns=0),
            lambda x: x.update(authority_granted=True),
        ):
            changed = copy.deepcopy(result)
            mutate(changed)
            with self.subTest(mutation=mutate):
                with self.assertRaises(audit.AuditFailure):
                    audit.audit_result(self.raw, changed, self.a03_oracle)


if __name__ == "__main__":
    unittest.main()
