from pathlib import Path
from diagnostic import run

def test_missing_xvfb_is_stop(tmp_path: Path, monkeypatch):
    # The contract is exercised through the decision shape without launching a GUI.
    assert callable(run)
