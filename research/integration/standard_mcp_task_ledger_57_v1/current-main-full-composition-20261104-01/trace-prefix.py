import multiprocessing
import runpy
import sys

def trace(frame, event, arg):
    if event == "line" and frame.f_code.co_name == "test_prearmed_cleanup_can_precede_retired_owners_queued_down" and frame.f_lineno == 3667:
        print("CANCEL_RECEIPT=" + repr(frame.f_locals.get("cancelled")), flush=True)
    return trace

if __name__ == "__main__":
    multiprocessing.freeze_support()
    sys.settrace(trace)
    sys.argv = ["unittest", "-v", "runtime.guarded_x11_v1.test_calc_symbolic_plan_v1", "runtime.guarded_x11_v1.test_calc_profile_v1", "runtime.guarded_x11_v1.test_calc_task_artifact_v1", "runtime.cli_v1.test_mcp_guarded", "runtime.cli_v1.test_mcp_owned_process"]
    runpy.run_module("unittest", run_name="__main__")