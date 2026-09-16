# Exact control-flow transcription of RuntimeClient.execute_handles from
# Git blob ace0366f2c5252c9dab3927c664cb58234b5ff03 at BASE 7f8376c8...
import time

def execute_handles(self, task, aliases):
    started = time.perf_counter_ns()
    first_check, _ = self.check(aliases["field"], [12, 19],
                                "check-field-" + task["task_id"])
    if not first_check["eligible"]:
        return {"status": "safe_yield", "reason": "missing_symbol",
                "completed_actions": 0, "started_ns": started,
                "ended_ns": time.perf_counter_ns()}
    entered = self.submit("enter-" + task["task_id"], [
        {"op": "pointer_click_target", "target_handle": aliases["field"],
         "offset": [12, 19], "button": 1, "duration_ms": 80},
        {"op": "chord", "modifier": "Control_L", "key": "a"},
        {"op": "text", "text": task["token"]},
        {"op": "settle", "quiet_ms": 80, "timeout_ms": 500},
    ])
    if entered["terminal"]["status"] != "completed":
        return {"status": "safe_yield", "reason": "execution_failed",
                "completed_actions": 0, "started_ns": started,
                "ended_ns": time.perf_counter_ns()}
    submit_check, _ = self.check(aliases["submit"], [12, 7],
                                 "check-submit-" + task["task_id"])
    if not submit_check["eligible"]:
        return {"status": "safe_yield", "reason": "missing_symbol",
                "completed_actions": 1, "started_ns": started,
                "ended_ns": time.perf_counter_ns()}
    saved = self.submit("submit-" + task["task_id"], [
        {"op": "pointer_click_target", "target_handle": aliases["submit"],
         "offset": [12, 7], "button": 1, "duration_ms": 80},
        {"op": "settle", "quiet_ms": 80, "timeout_ms": 500},
    ])
    status = "completed" if saved["terminal"]["status"] == "completed" else "safe_yield"
    return {"status": status,
            **({} if status == "completed" else
               {"reason": "execution_failed", "completed_actions": 1}),
            "started_ns": started, "ended_ns": time.perf_counter_ns()}
