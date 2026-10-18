import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import candidate
import audit


class ConstructionTests(unittest.TestCase):
    def setUp(self):
        self.fixture = json.loads((HERE / "fixture.json").read_text(encoding="utf-8"))

    def test_candidate_output_matches_independent_expected_ledger(self):
        registry = self.fixture["source_registry"]
        allowlist = self.fixture["priority_issuer_allowlist"]
        rows = [candidate.evaluate(c, registry, allowlist) for c in self.fixture["contexts"]]
        mutations = []
        import copy
        c = copy.deepcopy(self.fixture["contexts"][0]); c["rules"][0]["source"] = ""; mutations.append(("remove_source_span", c))
        c = copy.deepcopy(self.fixture["contexts"][0]); c["edges"][0]["issuer"] = "forged"; mutations.append(("forge_issuer", c))
        c = copy.deepcopy(self.fixture["contexts"][0]); c["rules"][0]["scope"]["target"] = "*"; mutations.append(("widen_scope", c))
        c = copy.deepcopy(self.fixture["contexts"][0]); c["edges"].append({"higher":"default","lower":"retry","issuer":"owner","authenticated":True,"current":True,"scope":c["scope"],"source":"s4"}); mutations.append(("insert_priority_cycle", c))
        c = copy.deepcopy(self.fixture["contexts"][7]); c["facts"]["retry_window"] = True; c["rules"][1]["kind"] = "STRICT"; c["edges"] = [{"higher":"broad","lower":"specific","issuer":"owner","authenticated":True,"current":True,"scope":c["scope"],"source":"s3"}]; mutations.append(("defeat_strict_prohibition", c))
        raw = {"case_count":len(rows),"rows":rows,"mutation_count":len(mutations),"mutations":[{"mutation":n,"result":candidate.evaluate(c,registry,allowlist)} for n,c in mutations]}
        self.assertEqual(audit.audit(raw)["status"], "PASS_METHOD_SCOPED")

    def test_invalid_priority_does_not_turn_into_a_permission(self):
        case = self.fixture["contexts"][3]
        row = candidate.evaluate(case, self.fixture["source_registry"], self.fixture["priority_issuer_allowlist"])
        self.assertEqual(row["status"], "UNKNOWN_STOP")
        self.assertEqual(row["obligations"], [])
        self.assertFalse(row["authority_changed"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
