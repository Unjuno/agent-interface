from pathlib import Path

RUNNER = Path(__file__).with_name("map01_recovery_cover_matched_v2_runner_3243_diagnostic.py")


def test_retained_wait_helper_present() -> None:
    source = RUNNER.read_text(encoding="utf-8")
    assert "def wait_retained" in source
    assert "fallback_terminal = session.wait_retained" in source
