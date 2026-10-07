import importlib.util
import pathlib
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


candidate = load("candidate")
auditor = load("auditor")
base = {"revision": 0, "agent_value": "original", "external_value": "old"}
cert = {"base_revision": 0, "agent_field": "agent_value", "agent_original": "original", "baseline_state": base}
obs0 = {"case_id": "baseline", "state": base, "certificate": cert, "journal": []}
assert candidate.classify(obs0) == {"decision": "NO_CHANGE", "proposal": None}
assert auditor.independent_decision({"state": base, "certificate": cert, "journal": []}) == candidate.classify(obs0)

disjoint = {"case_id": "disjoint", "state": {"revision": 1, "agent_value": "original", "external_value": "external-new"},
            "certificate": cert, "journal": [{"seq": 1, "revision": 1, "field": "external_value", "before_value": "old", "after_value": "external-new"}]}
assert candidate.classify(disjoint)["decision"] == "PROPOSE_COMPENSATION"
assert candidate.classify(disjoint)["proposal"] == {"restore_field": "agent_value", "restore_value": "original", "preserve_field": "external_value", "preserve_value": "external-new", "bind_revision": 1}
assert auditor.independent_decision(disjoint) == candidate.classify(disjoint)

mutants = [
    {**disjoint, "journal": []},
    {**disjoint, "journal": [{**disjoint["journal"][0], "seq": 2}]},
    {**disjoint, "journal": [{**disjoint["journal"][0], "after_value": "contradiction"}]},
    {**disjoint, "journal": [{**disjoint["journal"][0], "field": "agent_value", "before_value": "original", "after_value": "external-new"}], "state": {"revision": 1, "agent_value": "external-new", "external_value": "old"}},
]
for item in mutants:
    assert candidate.classify(item)["decision"] == "UNKNOWN"
    assert auditor.independent_decision(item) == candidate.classify(item)

errors = []
ids = ["baseline", "disjoint"]
assert auditor.unique_rows([{"case_id": "baseline"}, {"case_id": "disjoint"}], ids, "test", errors)
errors = []
auditor.unique_rows([{"case_id": "baseline"}, {"case_id": "baseline"}], ids, "test", errors)
assert "test:duplicate" in errors and "test:missing_or_unexpected" in errors
errors = []
auditor.unique_rows([{"case_id": "baseline"}, {"case_id": "unexpected"}], ids, "test", errors)
assert "test:missing_or_unexpected" in errors

for path in ROOT.glob("*.py"):
    compile(path.read_text(), str(path), "exec")
print("PASS_CONSTRUCTION: baseline, disjoint proposal, four fail-closed anomalies, cardinality controls, Python syntax")
