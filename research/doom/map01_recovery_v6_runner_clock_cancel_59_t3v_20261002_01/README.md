# T3V shared-clock runner boundary

Issue #6261; successor to #6252. The #6252 STOP package and allocation remain unchanged.

**Disposition: HOLD_D_CLOCK_RETURN_BOUND_AMBIGUOUS.** The one construction, one candidate invocation and one independent raw-only audit completed without retries. Candidate and auditor gates passed. The prose D gate's 50 ms reference point is ambiguous: exact return-to-release is 55.791 ms, while cancel-request-to-release is 36.166 ms. The frozen candidate and auditor operationalized the latter; under the stricter former reading, A exceeds the limit by 5.791 ms. Preserve the result as a HOLD rather than choose the favorable interpretation.

- [Frozen plan and H/T/D/C/U](PLAN.md)
- [Full report and exact boundaries](REPORT.md)
- [Freeze](FREEZE.json)
- [Construction raw receipt](results/construction_attempt.json)
- [Candidate raw trace](results/candidate_raw.json)
- [Independent audit](results/audit_result.json)
- [SHA-256 manifest](SHA256SUMS)

The experiment used exact current-main v6 runner, Executor-v10 and Lease Git objects in a host-only fake-session/fake-backend harness. It did not use a container, GUI, game, model/provider, network, GPU or physical input. Do not rerun this allocation; any clarification experiment needs a separately frozen successor.
