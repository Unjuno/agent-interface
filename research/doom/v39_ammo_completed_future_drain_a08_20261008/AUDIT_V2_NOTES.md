# A08 audit v2 correction

The original A08 audit v1 checked that `RESULT.json.main_order_lines` were increasing, but did not independently derive the reported locations from the frozen controller. A v2 auditor now reparses the frozen controller commit, locates the completed-future drain, `planner_result`, and following `final_action_admission`, verifies the guard condition, and requires exact equality with the result's line claims.

The original candidate, result, raw event stream, v1 audit, and v1 tests remain unchanged. This is a post-hoc audit correction; no candidate or live allocation was rerun. `test_audit_v2.py` mutates both ordered and single reported line claims and confirms rejection.
