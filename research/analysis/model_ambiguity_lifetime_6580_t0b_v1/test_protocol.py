import json
import tempfile
import unittest
from pathlib import Path

import auditor
import candidate


class DecisionGameTests(unittest.TestCase):
    def fixture(self, directory):
        p = Path(directory) / "candidate.json"
        candidate.main(p)
        return p, json.loads(p.read_text())

    def test_exact_decision_table_audits(self):
        with tempfile.TemporaryDirectory() as d:
            p, _ = self.fixture(d)
            result = auditor.audit(p)
            self.assertEqual(result["status"], "PASS_METHOD_SCOPED")
            self.assertEqual(result["rows_seen"], 48)

    def test_full_valid_receipt_supports_safe_reactive_continuation(self):
        with tempfile.TemporaryDirectory() as d:
            _, obj = self.fixture(d)
            row = next(r for r in obj["rows"] if r["lifetime"] == "FULL" and r["phase"] == "PRE_EVENT" and r["evidence"] == "VALID_1" and r["order"] == "AGENT_FIRST_REACTIVE")
            self.assertEqual((row["decision"], row["action"], row["prior_support"]), ("CONTINUE", "B", [1]))

    def test_stepwise_prior_does_not_authorize_reactive_continuation(self):
        with tempfile.TemporaryDirectory() as d:
            _, obj = self.fixture(d)
            row = next(r for r in obj["rows"] if r["lifetime"] == "ZERO" and r["evidence"] == "VALID_0" and r["order"] == "AGENT_FIRST_REACTIVE")
            self.assertEqual((row["decision"], row["prior_support"]), ("YIELD", [0, 1]))

    def test_event_receipt_binds_only_after_declared_event(self):
        with tempfile.TemporaryDirectory() as d:
            _, obj = self.fixture(d)
            rows = [r for r in obj["rows"] if r["lifetime"] == "EVENT" and r["evidence"] == "VALID_0" and r["order"] == "AGENT_FIRST_REACTIVE"]
            pre = next(r for r in rows if r["phase"] == "PRE_EVENT")
            post = next(r for r in rows if r["phase"] == "POST_EVENT")
            self.assertEqual((pre["decision"], post["decision"]), ("YIELD", "CONTINUE"))

    def test_stale_evidence_never_narrows(self):
        with tempfile.TemporaryDirectory() as d:
            _, obj = self.fixture(d)
            stale = [r for r in obj["rows"] if r["evidence"] == "STALE"]
            self.assertTrue(all(r["prior_support"] == [0, 1] for r in stale))

    def test_mutation_controls_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p, obj = self.fixture(d)
            mutations = []
            # Full-stickiness evidence incorrectly discarded.
            m=json.loads(json.dumps(obj)); m["rows"][0]["prior_support"]=[0,1]; mutations.append(m)
            # Stepwise model improperly carries old observation forward.
            m=json.loads(json.dumps(obj)); i=next(i for i,r in enumerate(m["rows"]) if r["lifetime"]=="ZERO" and r["evidence"]=="VALID_0" and r["order"]=="AGENT_FIRST_REACTIVE"); m["rows"][i]["decision"]="CONTINUE"; m["rows"][i]["action"]="A"; mutations.append(m)
            # Premature event commitment.
            m=json.loads(json.dumps(obj)); i=next(i for i,r in enumerate(m["rows"]) if r["lifetime"]=="EVENT" and r["phase"]=="PRE_EVENT" and r["evidence"]=="VALID_0" and r["order"]=="AGENT_FIRST_REACTIVE"); m["rows"][i]["prior_support"]=[0]; mutations.append(m)
            # Stale evidence narrows a set.
            m=json.loads(json.dumps(obj)); i=next(i for i,r in enumerate(m["rows"]) if r["evidence"]=="STALE"); m["rows"][i]["prior_support"]=[0]; mutations.append(m)
            # Nature reacts after the proposed action but gate continues.
            m=json.loads(json.dumps(obj)); i=next(i for i,r in enumerate(m["rows"]) if r["lifetime"]=="ZERO" and r["evidence"]=="MISSING" and r["order"]=="AGENT_FIRST_REACTIVE"); m["rows"][i]["decision"]="CONTINUE"; m["rows"][i]["action"]="A"; mutations.append(m)
            # False unsafe dispatch.
            m=json.loads(json.dumps(obj)); m["rows"][1]["unsafe_dispatch"]=True; mutations.append(m)
            # Negative-control regression.
            m=json.loads(json.dumps(obj)); m["negative_controls"][0]["decision"]="YIELD"; mutations.append(m)
            for i, mutation in enumerate(mutations):
                p.write_text(json.dumps(mutation))
                with self.subTest(mutation=i):
                    self.assertEqual(auditor.audit(p)["status"], "FAIL_METHOD")


if __name__ == "__main__":
    unittest.main()
