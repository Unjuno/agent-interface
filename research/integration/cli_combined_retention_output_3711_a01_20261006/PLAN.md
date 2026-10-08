# #3711 A01 combined report-persistence + stdout-loss boundary

H: If report persistence and stdout delivery fail in the same CLI dispatch, the retained attempt must remain non-replayable and distinguishable as incomplete; a caller must not infer no action from the nonzero process exit.

T: Four conditions x two repetitions = 8 fresh subprocess cases: REPORT_OK/STDOUT_OK, REPORT_FAIL/STDOUT_OK, REPORT_OK/STDOUT_CLOSED, REPORT_FAIL/STDOUT_CLOSED. Synthetic completed dispatch only; no GUI/native input/model/network. Source-faithful adapter copies current-main attempt.invoke/_write_json and __main__._emit/_present_result logic relevant to this boundary. Actual OS pipe closure is used for STDOUT_CLOSED. Report failure is injected at the final os.replace for report.json after request publication and synthetic dispatch completion. One formal allocation, no rerun/replacement.

D: PASS_COMBINED_RETENTION_OUTPUT_BOUNDARY_SCOPED iff all 8 cases complete; REPORT_OK cases have final report.json and report_recorded; REPORT_FAIL cases have no final report, complete .report.json.tmp, unknown_or_incomplete, replay_allowed=false; STDOUT_CLOSED cases exit nonzero with BrokenPipe; STDOUT_OK+REPORT_FAIL emits retention.report_persisted=false and returns code 2; every synthetic dispatch count is exactly 1; no case authorizes replay. Independent raw-only audit errors=[] and 8 effective corruptions reject.

C: Synthetic dispatch result, source-faithful copied logic rather than full installed current-main package; filesystem and pipe faults are directed; no native effect is produced. This isolates state composition only.

U: Does not establish real GUI effect, arbitrary storage faults, power loss, current portable zipapp packaging parity, natural rate, latency/token benefit, or product readiness. Same-author separate auditor is not external review.
