from pathlib import Path
from audit_source_bundle import audit

def test_missing_runtime_is_a_typed_stop(tmp_path: Path):
    (tmp_path / "research/integration/golden_v3_second_domain_2246_v1").mkdir(parents=True)
    (tmp_path / "runtime").mkdir()
    result = audit(tmp_path)
    assert result["decision"] == "STOP_SOURCE_BUNDLE"
    assert any(reason.startswith("missing_required:") for reason in result["reasons"])

def test_complete_bundle_passes(tmp_path: Path):
    required = (
        "research/integration/golden_v3_second_domain_2246_v1/formal_matrix_runner.py",
        "research/integration/golden_v3_second_domain_2246_v1/gtk_fixture_app.py",
        "research/integration/golden_v3_second_domain_2246_v1/formal_matrix_2606/matrix_gate.py",
        "runtime/cli_v1/golden_v3.py",
        "runtime/core_v1/contract.py",
    )
    for item in required:
        path = tmp_path / item
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("", encoding="utf-8")
    result = audit(tmp_path)
    assert result["decision"] == "PASS_SOURCE_BUNDLE_FREEZE"
    assert set(result["hashes"]) == set(required)
