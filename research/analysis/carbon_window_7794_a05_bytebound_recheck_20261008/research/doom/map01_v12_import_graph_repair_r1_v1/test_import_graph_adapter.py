from pathlib import Path
from import_graph_adapter import live_control_backend


def test_live_control_import_identity():
    root = Path(__file__).resolve().parents[3]
    with live_control_backend(root) as v8:
        assert v8.Backend.__module__ == "session_v8"
        assert v8.__file__.endswith("research/live_control/session_v8.py")


if __name__ == "__main__":
    test_live_control_import_identity()
    print("IMPORT_GRAPH_SMOKE_PASS")