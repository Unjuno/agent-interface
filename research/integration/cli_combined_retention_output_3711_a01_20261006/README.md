# #3711 A01 — combined report-persistence + stdout-loss evidence

Prospective local construction/boundary allocation executed on 2026-10-06 against current-main source semantics. Source/gates were locally frozen before the 8-case formal allocation; publication follows execution, so this is not GitHub preregistration.

Disposition: `PASS_COMBINED_RETENTION_OUTPUT_BOUNDARY_SCOPED`.

This is a synthetic dispatch composition test. It uses source-faithful copies of current-main `attempt.invoke/_write_json/inspect_attempt` and `__main__._emit/_present_result` logic, plus an actual OS closed stdout pipe. It does **not** execute a GUI/native backend, model, or task effect.

The full 55-member evidence package is embedded losslessly as `EVIDENCE.b64`. Restore with `python -S -B restore.py`, then inspect `formal/AUDIT.json`, `CONTROLS.json`, and the per-case raw directories. No candidate/formal rerun is performed by restoration.

Key finding: when report persistence fails and stdout is also closed, the child exits nonzero with `BrokenPipeError`, while retained state remains `unknown_or_incomplete`, `replay_allowed=false`, `process_state=unknown`, the request is recorded, the final report is missing, and the complete temporary report residue is visible. Synthetic dispatch count is exactly one. Therefore a nonzero CLI exit is not evidence that dispatch did not occur and does not authorize replay.

Current-main source commit used for the source-bound check: `a3e6b0c1ab8d6af5c24abb88a451ce41c4ede028`. Current `runtime/cli_v1/attempt.py` blob recorded at freeze: `bd1725a18b6aef6f45c62297cbd794c760ea0a9f`.

Scope limits: directed filesystem fault, synthetic completed dispatch, no full current-main package execution, no native input/effect, no power-loss/fsync/disk-full claim, no natural failure rate, no performance/token claim. Same-author separate raw audit is not external human review. #3711 remains open.
