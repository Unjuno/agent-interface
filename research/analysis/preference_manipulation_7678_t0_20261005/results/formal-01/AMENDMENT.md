# Append-only outcome correction

**Amendment status: HOLD — formal result is not eligible for PASS.** This correction supplements the preregistration, FREEZE, RUN, and raw outputs. It does not edit or replace those historical files.

The first formal candidate process completed with exit code 0 and wrote `candidate-output.json`. The first auditor process exited 1 because `FREEZE.json` lacked the expected `fixture_sha256` field. The audit implementation was then modified after freeze: first to supply the missing field, then to project delegate preferences over the eligible alternatives in constrained control cases. A subsequent manual auditor invocation completed with exit code 0 and printed `PASS_METHOD_SCOPED` against the retained candidate output.

The freeze record itself was also amended after execution to add `fixture_sha256` and to refresh file digests; the preregistration text and the runner were edited after formal execution as well. The original pre-amendment `FREEZE.json` bytes were not separately retained. The current freeze file therefore cannot prove that the audited code/procedure matches the exact preregistered state. This is an additional reason for HOLD, not a repair to the allocation.

That post-freeze auditor run is a diagnostic recovery, not the preregistered independent audit. Therefore the PASS line in `audit-output.json` and the zero exit code now present in `RUN.json` are preserved as historical outputs but **must not be treated as a valid formal PASS**. The frozen experiment outcome is HOLD because the frozen audit procedure was not successfully executed as frozen. No fresh allocation or candidate rerun is authorized by this amendment.

The corrected auditor's comparison and counts may guide a future, newly preregistered allocation, but they do not retroactively repair this allocation's confirmatory result. Preserve the initial failure in `INITIAL_RUN_FAILURE.json`, all stdout/stderr, and all candidate/audit JSON as-is. Do not write a summary that promotes the diagnostic recovery to a formal result.

The result files' integrity manifest was removed because a truthful manifest would need to be append-only and distinguish immutable candidate output, first failed audit, and later diagnostic recovery. No `REPORT.md` is issued. The corresponding GitHub Issue was not updated by this experiment.
