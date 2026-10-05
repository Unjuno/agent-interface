"""Read-only audit for the retained Win32 host smoke result."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
result = json.loads((HERE / "result.json").read_text(encoding="utf-8"))
rows = result.get("transitions", [])
assert result["schema"] == "win32-key-transition-host-smoke-a01-v1"
assert result["outcome"] == "PASS_SCOPED"
assert result["preconditions"]["probe_hwnd_foreground"] is True
assert result["preconditions"]["shift_initially_down"] is False
assert len(rows) in (2, 3)
down = rows[0]
explicit_up = rows[1]
assert [down["operation"], explicit_up["operation"]] == ["down", "up"]
assert down["cleanup"] is False and explicit_up["cleanup"] is False
assert down["key"] == explicit_up["key"] == "SHIFT"
assert down["hold_id"] == explicit_up["hold_id"]
assert down["backend_instance_id"] == explicit_up["backend_instance_id"]
assert [down["operation_index"], explicit_up["operation_index"]] == [0, 1]
assert down["os_key_state_classification"] == "OS_KEY_STATE_DOWN_CONFIRMED"
assert explicit_up["os_key_state_classification"] == "OS_KEY_STATE_UP_CONFIRMED"
assert down["state_before"]["down"] is False and down["state_after"]["down"] is True
assert explicit_up["state_before"]["down"] is True and explicit_up["state_after"]["down"] is False
if len(rows) == 3:
    cleanup_up = rows[2]
    assert cleanup_up["operation"] == "up" and cleanup_up["cleanup"] is True
    assert cleanup_up["hold_id"] == down["hold_id"]
    assert cleanup_up["os_key_state_classification"] == "OS_KEY_STATE_ALREADY_UP"
    assert cleanup_up["state_after"]["down"] is False
assert all(row["physical_keyboard_state_proven"] is False for row in rows)
assert all(row["application_delivery_proven"] is False for row in rows)
assert all(row["sendinput_acknowledged_ns"] >= row["requested_ns"] for row in rows)
assert all(row["os_state_change_window_ns"] for row in rows[:2])
assert result["release"]["verified"] is True
assert result["release"]["keys_down"] == []
assert result["release"]["buttons_down"] == []
print("PASS_AUDIT_WIN32_HOST_SMOKE_SCOPED")
