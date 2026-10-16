# #3711 A01 — combined report-persistence and stdout-loss boundary

Disposition: **PASS_COMBINED_RETENTION_OUTPUT_BOUNDARY_SCOPED**.

Eight first-outcome subprocess cases (four fault combinations × two repetitions) completed with no formal rerun or replacement. The experiment used a source-faithful adapter of current-main `runtime/cli_v1/attempt.py` retention logic and `runtime/cli_v1/__main__.py` `_emit/_present_result` behavior, plus an actual closed OS stdout pipe. Synthetic dispatch returned one completed report per case; no GUI/native input/model/network was used.

Key result: when report publication fails and stdout is also closed, the child exits nonzero with BrokenPipe while the retained attempt remains `unknown_or_incomplete`, `replay_allowed=false`, `process_state=unknown`, request recorded, final report missing, and complete `.report.json.tmp` residue visible. The synthetic dispatch count remains exactly one. When report publication fails but stdout is available, the CLI projection carries `report_persisted=false` and returns code 2. A nonzero process exit therefore cannot be used as evidence that dispatch did not occur or as replay authority.

Raw-only audit: 94 checks, errors=[]. Eight effective copied-evidence mutations were all rejected. Scope is composition semantics only: source-faithful copied logic, synthetic dispatch, directed filesystem fault, no full current-main package/native effect/power-loss claim.
