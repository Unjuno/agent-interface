# Append-only outcome correction

**Amendment status: HOLD — formal result is not eligible for PASS.** This correction supplements the preregistration, FREEZE, RUN, and raw outputs. It does not edit or replace those historical files.

The first formal candidate process completed with exit code 0 and wrote `candidate-output.json`. The first auditor process exited 1 because `FREEZE.json` lacked the expected `fixture_sha256` field. Its original stdout/stderr were not retained; the prior package version contained only the later diagnostic stdout and an empty stderr file. `INITIAL_RUN_FAILURE.json` is a retrospective account, not a raw stream. The audit implementation was then modified after freeze: first to supply the missing field, then to project delegate preferences over the eligible alternatives in constrained control cases. A subsequent manual auditor invocation completed with exit code 0 and printed `PASS_METHOD_SCOPED` against the retained candidate output.

The freeze record itself was also amended after execution to add `fixture_sha256` and to refresh file digests; the preregistration text and the runner were edited after formal execution as well. The original pre-amendment `FREEZE.json` bytes were not separately retained. The current freeze file therefore cannot prove that the audited code/procedure matches the exact preregistered state. This is an additional reason for HOLD, not a repair to the allocation.

That post-freeze auditor run is a diagnostic recovery, not the preregistered independent audit. Therefore the PASS line in `audit-output.json` and the zero exit code now present in `RUN.json` are preserved as historical outputs but **must not be treated as a valid formal PASS**. The frozen experiment outcome is HOLD because the frozen audit procedure was not successfully executed as frozen. No fresh allocation or candidate rerun is authorized by this amendment.

The corrected auditor's comparison and counts may guide a future, newly preregistered allocation, but they do not retroactively repair this allocation's confirmatory result. Preserve `INITIAL_RUN_FAILURE.json`, the available later diagnostic stdout/empty stderr, and all candidate/audit JSON as-is; the missing first-audit stdout/stderr cannot be recovered from this package. Do not write a summary that promotes the diagnostic recovery to a formal result.

The result files' integrity manifest was removed because a truthful manifest would need to be append-only and distinguish immutable candidate output, first failed audit, and later diagnostic recovery. No `REPORT.md` is issued. `RUN.json` now exposes the authoritative `HOLD` disposition and labels the later PASS as diagnostic; this is a reviewer-requested disposition correction, not a rerun or retroactive repair. The corresponding GitHub Issue was not updated by this experiment.

## Addendum — reviewer correction, diagnostic only

The current `FREEZE.json` bytes before this addendum are preserved verbatim as
`FREEZE_POSTRUN_PRE_REVIEW.json`; its SHA-256 is recorded in the adjacent
`.sha256` file. This is the already-amended post-run freeze record, not a
recovery of the unavailable original pre-run bytes.

The PR review found that the README digest in that amended freeze no longer
matched the current README and that `summarize_manipulation()` trusted
candidate-authored order tiers and partial signals. The additive correction
updates only the diagnostic source-hash map and makes the auditor independently
reconstruct orders, reports, and partial signals from rank vectors and the
fixture before summarizing. Mutation tests verify corrupted order tiers or
partial signals are rejected. A single post-run diagnostic audit is written to
`results/review-correction-01/`; it does not overwrite candidate output or the
earlier diagnostic audit. Its result remains non-confirmatory. `RUN.json` stays
`HOLD`, no candidate or allocation rerun occurred, and the first auditor's
missing stdout/stderr remain unrecoverable.

The first attempt to run this review-correction diagnostic exited 1 before
creating its output because a post-run JSON serialization command malformed
`FREEZE.json`. The structured failure record is
`results/review-correction-01/ATTEMPT.json`; stdout/stderr for that attempt were
not separately retained, so this is not represented as a raw log. The invalid
post-run file was reconstructed from the byte-preserved pre-review copy, then
the diagnostic digest entries were refreshed. No candidate output or formal
allocation was rerun or changed. Any subsequent corrected diagnostic is
separately identified and remains non-confirmatory.


The next diagnostic attempt exited 1 at frozen-file preflight on COMMANDS.txt. Its stdout/stderr are preserved under results/review-correction-02/. This exposed Windows checkout newline conversion: Git blob hashes matched the earlier freeze, while working-copy CRLF bytes did not. A package-local .gitattributes now disables text conversion, frozen sources are restored to their original LF bytes where unchanged, and formal result files retain their existing bytes. This was an auditor-only diagnostic preflight; no candidate output or formal allocation was rerun.


The corrected reviewer diagnostic in results/review-correction-03/AUDIT.json completed with PASS_METHOD_SCOPED and found no order/report/world mapping mismatch. The independent mapping reconstruction and corruption tests passed. This is a post-run diagnostic against retained candidate output; RUN.json remains HOLD and no formal result has been promoted.
