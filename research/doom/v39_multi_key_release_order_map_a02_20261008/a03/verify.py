"""Independent audit of A03 output and its pinned production validator."""
import ast
import hashlib
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
V19_SHA = "2c5304bd246118f8124d5f7b50b81f869fb35ea3ee76887f4682748fdf95618a"
SCORER_SHA = "48518dd27d8271c2b9be271b0e48bd2827240a53883d07713563faa6e7e731cc"


def main():
    v19 = (ROOT / "session_map01_v19.py").read_bytes()
    scorer_path = ROOT / "map01_scorer_stdio_adapter_v3.py"
    scorer = scorer_path.read_bytes()
    assert hashlib.sha256(v19).hexdigest() == V19_SHA
    assert hashlib.sha256(scorer).hexdigest() == SCORER_SHA
    rows = [json.loads(line) for line in (ROOT / "INPUT_EVENTS.jsonl").read_text(encoding="utf-8").splitlines()]
    down = next(row for row in rows if row.get("event") == "input_admission")
    up = next(row for row in rows if row.get("event") == "input_release_measurement")
    assert "actuation_id" not in down
    assert down["physical_key_measurement"]["actuation_id"]
    assert down["physical_key_measurement"]["adapter_edge"]["actuation_id"] == down["physical_key_measurement"]["actuation_id"]

    tree = ast.parse(scorer, filename=str(scorer_path))
    wanted = {"_need", "_exact_ns", "_measure", "validate_measured_release_pair"}
    nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in wanted]
    assert {node.name for node in nodes} == wanted

    class ProductionError(ValueError):
        pass

    namespace = {"MeasuredReleaseBoundary": lambda **values: values, "MeasuredReleaseError": ProductionError}
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])), str(scorer_path), "exec"), namespace)
    validate = namespace["validate_measured_release_pair"]

    result = json.loads((ROOT / "result.json").read_text(encoding="utf-8"))
    assert result["source"]["v19_sha256"] == V19_SHA
    assert result["source"]["scorer_sha256"] == SCORER_SHA
    assert result["source"]["raw_event_count"] == len(rows) == 2
    assert result["identity"] == ["id", "step", "owner_id", "intent_token", "key", "physical_key_measurement.actuation_id"]
    assert result["candidate_schema_compatible"] is True
    totals = 0
    for case in result["cases"]:
        n = case["key_count"]
        keys = tuple(chr(ord("A") + i) for i in range(n))
        expected = {(a, r) for a in itertools.permutations(keys) for r in itertools.permutations(keys)}
        observed = {(tuple(row["admission_order"]), tuple(row["release_order"])) for row in case["schedules"]}
        assert observed == expected
        assert case["schedule_count"] == len(expected)
        assert case["valid_scorer_boundaries"] == len(expected)
        assert case["invalid_or_censored"] == 0
        for row in case["schedules"]:
            assert row["candidate_down_key"] == row["candidate_up_key"] == row["release_order"][-1]
            assert row["candidate_has_event_actuation_id"] is False
            assert row["held_after"] == [] and row["scorer_boundary_valid"] is True
            assert row["scorer_boundary"]["key"] == row["release_order"][-1]
            assert row["scorer_boundary"]["actuation_id"] == f"act-{row['release_order'][-1]}"
            totals += 1
    assert totals == 41
    controls = result["mutation_checks"]
    assert len(controls) == 6 and all(value is True for value in controls.values())
    print("independent audit: PASS (2 pinned source hashes; producer schema; 41 schedules; 6 mutation controls)")


if __name__ == "__main__":
    main()
