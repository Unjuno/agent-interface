# G10 save-request chronology candidate (2026-11-15)

## Finding and change

The candidate G10 save-controller receipt previously accepted `save_request_monotonic_ns == transition.execution_accepted_ns`. The compiled core samples `execution_accepted_ns` after the executor returns, validates the action terminal, and confirms release. Equality therefore did not prove that the save request preceded action completion.

`make_registered_calc_g10_save_controller_receipt` now requires:

`transition.execution_started_ns <= save_request_monotonic_ns < transition.execution_accepted_ns`

The fake composition test timestamps the request at the fake execution adapter entry, using `time.perf_counter_ns`, the same clock used by the compiled X11 adapter. A negative unit case rejects a request timestamp equal to accepted time. FODS remain archived fixtures; no Calc GUI or live workbook was used.

## Verification

Environment: Python 3.11.9, Microsoft Windows 11 Pro, local candidate worktree.

~~~powershell
python -m unittest runtime.guarded_x11_v1.test_calc_g10_artifact_v1 runtime.guarded_x11_v1.test_calc_g10_action_custody_composition
python -O -m unittest runtime.guarded_x11_v1.test_calc_g10_artifact_v1 runtime.guarded_x11_v1.test_calc_g10_action_custody_composition
git diff --check
~~~

Results: 13/13 passed normally (1.902 s) and 13/13 under `-O` (1.121 s). Logs are `normal.log` and `optimized.log`.

## SHA-256

- `normal.log`: `6FA2B213A8CACBEDE8B8084757D1EB497201BE3593F0604DD179E1DB56612133`
- `optimized.log`: `3745283DF0E2D69D78E752D287AF24B2C71E1C49E085D8208D6414C79C3D3113`
- `runtime/guarded_x11_v1/calc_g10_artifact_v1.py`: `65039F1B3928B51A0A9AEFBBA04948A38C77D24B3AA6DD511FE91C8E5AB8BF98`
- `runtime/guarded_x11_v1/test_calc_g10_artifact_v1.py`: `35356BE835CD7A2D939028D1BAA9601FA44F22687B1F8D0182FC13864ECD42DD`
- `runtime/guarded_x11_v1/test_calc_g10_action_custody_composition.py`: `5CE7738F5FC6874971392CB2B524B54FBE88C12DE61627C834B0330D0C392645`
- `docs/CURRENT_GOAL.md`: `4FA804F0FD02A67362C0B7877179A2697D097531DB5A96CDF73120C125BC0396`

This is local offline evidence only. G10 is not registered through the public MCP preparation/compiled path, and no live Calc, model-token, or #57 economics result follows.
