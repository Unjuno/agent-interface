"""Pure preformal harness checks for Issue #869; no X11 input is emitted."""
from __future__ import annotations

import run_block
import run_case_v2


def test_release_filter_keeps_only_release_rpc() -> None:
    class Backend:
        pass

    def fake_loader(owner, lease, case_id, all_rows):
        backend = Backend()
        backend.emit = all_rows.append
        return backend

    original = run_case_v2._original_loader
    run_case_v2._original_loader = fake_loader
    try:
        measured: list[dict] = []
        backend = run_case_v2._release_only_loader(None, None, "case", measured)
        backend.emit({"event": "input_admission", "id": "case"})
        backend.emit({"event": "input_release_rpc", "id": "case"})
        assert measured == [{"event": "input_release_rpc", "id": "case"}]
    finally:
        run_case_v2._original_loader = original


def test_formal_gate_is_closed() -> None:
    assert run_block.FREEZE["formal_authorized"] is False
    try:
        run_block.main()
    except RuntimeError as exc:
        assert "formal allocation blocked" in str(exc)
    else:
        raise AssertionError("formal block unexpectedly executable")


if __name__ == "__main__":
    test_release_filter_keeps_only_release_rpc()
    test_formal_gate_is_closed()
    print("PASS_PREFORMAL_HARNESS")
