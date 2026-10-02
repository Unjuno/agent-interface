from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

import audit
import candidate


ROOT = Path(__file__).parent


class EnvelopeContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = json.loads((ROOT / "fixture.json").read_text(encoding="utf-8"))

    def candidate_result(self) -> dict:
        displays = [candidate.render(row) for row in self.fixture["checkpoints"]]
        return {"schema": "autonomy-envelope-candidate-v1", "fixture_sha256": candidate.hashlib.sha256((ROOT / "fixture.json").read_bytes()).hexdigest(), "checkpoint_count": len(displays), "displays": displays}

    def audit_result(self, value: dict) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "candidate.json"
            path.write_bytes(candidate.canonical_bytes(value) + b"\n")
            return audit.audit(ROOT / "fixture.json", path)

    def test_all_ten_source_bound_rows_match_independent_oracle(self) -> None:
        result = self.candidate_result()
        self.assertEqual(10, result["checkpoint_count"])
        audited = self.audit_result(result)
        self.assertEqual("PASS_METHOD_SCOPED", audited["result"], audited)

    def test_expected_critical_states(self) -> None:
        rows = {d["checkpoint_id"]: d for d in self.candidate_result()["displays"]}
        self.assertEqual("MODEL_DECIDING", rows["model-wait-valid-cover"]["state"])
        self.assertEqual("LOCAL_ACTION_ACTIVE", rows["local-action-active"]["state"])
        self.assertEqual("WAITING_FOR_EVIDENCE", rows["late-evidence-old-generation"]["state"])
        self.assertEqual("RELEASE_VERIFYING", rows["focus-revoked-release-pending"]["state"])
        self.assertEqual("YIELDING", rows["lease-expired-release-verified"]["state"])
        self.assertEqual("RELEASE_VERIFYING", rows["cancel-before-release-receipt"]["state"])
        self.assertEqual("TERMINAL/UNKNOWN", rows["unknown-actor-and-footprint"]["state"])
        self.assertEqual("TERMINAL", rows["terminal-all-obligations-verified"]["state"])
        self.assertNotEqual("TERMINAL", rows["terminal-incomplete-obligations"]["state"])

    def test_rejects_frozen_semantic_and_provenance_mutations(self) -> None:
        mutations = []
        def changed(fn):
            x = copy.deepcopy(self.candidate_result())
            fn(x)
            mutations.append(x)
        changed(lambda x: x["displays"][0]["permitted_next_action_classes"].append("CLICK"))
        changed(lambda x: x["displays"][2].update(state="LOCAL_ACTION_ACTIVE", permitted_next_action_classes=["CLICK"]))
        changed(lambda x: x["displays"][4].update(state="LOCAL_ACTION_ACTIVE", permitted_next_action_classes=["CLICK"]))
        changed(lambda x: x["displays"][3].update(physical_release_state="VERIFIED"))
        changed(lambda x: x["displays"][9].update(state="TERMINAL"))
        changed(lambda x: x["displays"][1]["target_footprint"].append("window:other"))
        changed(lambda x: x.update(fixture_sha256="0" * 64))
        changed(lambda x: x["displays"].pop())
        for index, mutant in enumerate(mutations):
            with self.subTest(mutation=index):
                self.assertEqual("FAIL_METHOD", self.audit_result(mutant)["result"])

    def test_no_display_claims_consent_or_future_action_commitment(self) -> None:
        forbidden = {"consent", "human_approved", "will_execute", "action_succeeded"}
        for display in self.candidate_result()["displays"]:
            self.assertTrue(forbidden.isdisjoint(display))


if __name__ == "__main__":
    unittest.main()
