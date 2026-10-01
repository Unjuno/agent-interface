# Retained Inkscape effect and document-preservation evidence (#34)

## Publication chronology

This is **retrospective publication on 2026-09-22** of the preceding conversation's completed `inkscape-preserved-document-34-20260922-01` allocation. It is not a new formal experiment or GitHub preregistration. The original local source freeze is dated `2026-09-21T22:19:14.212010+00:00`; original main was `e4c2e58122aa138e421048d8e86ec18259143b9e`.

`REPORT.md`, `SUMMARY.json`, `FREEZE.json`, `PREREG.md` and the scientific source copies here are verbatim historical files. In particular, their `STOP_GITHUB_WRITE_CAPABILITY_UNAVAILABLE`, `github_pr_created=false` and `formal_started=false` fields describe their original recording times, not current publication status. They have not been retroactively edited. The present continuation has working GitHub writes and is delivering the same evidence under existing Issue #34, comment 5768655259. No publication-only successor Issue, new application run or formal rerun was created.

Intake main: `2308b8301d69b7089a2e0636486736ed59b61537`. README, CURRENT_GOAL, ROADMAP, open Issues/PRs, closed #2076, #34 comments and 138 returned branch names were inspected. Exact-path Issue and open Inkscape PR searches returned no match; unpushed work remains unknown. Older evidence delivery under #4007 and the separate request/event-scope branch are not duplicated. Only this additive namespace changes; shared runtime, workflows, root documents, earlier evidence and other workers' branches are untouched.

## Executed result and interpretation

**PASS_INKSCAPE_PRESERVED_DOCUMENT_SCOPED**, not a production promotion. The target-only comparator remains **FAIL_REQUIRED_ONLY_COMPLETION_POLICY**.

| Retained quantity | Value |
| --- | ---: |
| Fresh formal documents | 24 |
| Reporting views (not independent app trials) | 72 |
| Actual Inkscape subprocesses / zero exits | 96 / 96 |
| Full-contract complete / partial / failure | 3 / 12 / 9 |
| Target-only complete / false full completion | 15 / 12 |
| Missing or mismatched evidence views returning UNKNOWN | 48 / 48 |
| Full-pixel-equal correct/duplicate pairs with object counts 2 vs 3 | 3 |
| Formal allocations / fixed batches / reruns | 1 / 3 / 0 |

The task moves one rectangle right by 30 SVG user units while preserving the target color, the other rectangle's geometry/color and the object-ID set. Both-object movement, deletion, recoloring and overlaid duplication demonstrate why the required effect alone is insufficient. Exact equal rendering does not prove equal document structure. No-effect, wrong-object and half-distance controls remain failures. These are directed conditions, not natural failure probabilities or a claim of an Inkscape defect.

The exact closed-#2076 reducer (Git blob `3ccf652575837c5ab961e78b8e9d56c703f4187e`) is unchanged. The new, restricted saved-document adapter obtains per-invariant evidence; its `PARTIAL_REQUIRED_EFFECT_ONLY` presentation explicitly maps the historical reducer's `PARTIAL_PRIMARY_RESTORED` label without asserting a restoration took place.

## H / T / D / C / U

- **H:** a correct primary effect does not establish preserved document invariants; a document-bound verifier can distinguish complete, partial, failed and unknown outcomes.
- **T:** eight conditions, three repetitions, 24 new SVGs; before-query, action/save, after-query and PNG render in separate actual Inkscape processes; 16 construction documents excluded; three prospectively fixed formal batches.
- **D:** every document/view/process/source/byte identity, frozen outcome gate, three raster-equivalence witnesses and independent audit must reconcile. Preserve the comparator's negative finding and all first outcomes.
- **C:** a weaker task allowing collateral edits could legitimately use a weaker verifier. No equal-cost superiority, causal necessity or generic image-verification failure is inferred.
- **U:** one Inkscape version and a bounded flat opaque-rectangle SVG contract, trusted private files and no concurrent editing. Arbitrary SVG/CSS, real pointer/keyboard routes, Calc, model decisions, authentication, cost/latency and production acceptance remain untested.

The full original variable table, conditional reasoning, unit checks, environment, controls and stop rules are in PREREG.md and the restored source tree. Timestamps are diagnostic; no calibrated combined timing uncertainty or performance gate is claimed.

## Exact evidence retention

`ARCHIVE.json` and eight binary parts reconstruct **all 784 original study files / 1,806,567 bytes**. This includes exact frozen sources, construction records and failures, every formal SVG/PNG/query/stdout/stderr/process receipt, original audits and original SHA256SUMS. PNGs are restored byte-for-byte, not re-encoded. No member is regenerated from a formula or simulation.

The bounded XZ tagged-file-map is 89,208 bytes, SHA-256:

`4eb763fe3c54cc234992abdd3db722d2d3c4ace613859d2c1d967b4c28897a73`

The original 2,783,006-byte conversation handoff ZIP has SHA-256:

`9b8d948c061d44cd1f5df490f8920b26510156c25b8163a38d611ad6224d67c1`

That larger outer ZIP also includes redundant patches, additional outer delivery diagnostics and a nested earlier-study ZIP. Those redundant outer/nested copies are **not** re-uploaded here; the complete 784-member Inkscape scientific tree is. The original whole handoff remains a separate conversation artifact. Hashes are integrity commitments, not authentication.

## Read-only reproduction

Requirements: Python standard library plus Pillow for the original raw auditor; the recorded environment used CPython 3.13.5 / Pillow 12.3.0. No Inkscape, X display, model, Docker, input or network is needed for these checks. Run from this publication directory with new output paths:

```sh
python -B -m unittest -v test_unpack
python -B unpack.py /tmp/inkscape34-review
cd /tmp/inkscape34-review
sha256sum -c SHA256SUMS
python -B audit.py formal-01 --report /tmp/inkscape34-reaudit.json --controls
python -B compare_audit_outputs.py AUDIT.json /tmp/inkscape34-reaudit.json
python -B -m unittest -v test_consumer
```

The restorer validates bounded part/whole-archive identities, normalized relative member names and the full original manifest before writing to a new private destination; it does not import or execute archived code. `test_unpack` is postformal publication engineering, not a scientific allocation. Use a trusted private checkout/destination; the restorer is not a hostile-filesystem concurrency protocol.

The readable scientific source copies at this directory's top level are for inspection. Restore the complete tree before running the original auditor. **Do not run `run_batch.py` or `execute_batch.py` with the consumed formal identity.** Their presence preserves reproducibility and provenance, not permission for a silent repeat.

## Continuation validation and retained limitations

All 783 original SHA256SUMS entries match. A fresh restoration reproduced every original member byte; the unchanged raw-only auditor returned the same 24-case scientific result, zero errors and 14/14 rejected semantic mutations. All 15 unit tests pass. Seven packaging refusal controls pass; VALIDATION.json records the continuation's scope. Formal and Inkscape invocations in this continuation are zero.

One malformed-PNG negative-control error includes the process-specific address of a BytesIO object. Whole-audit byte identity is therefore **not** claimed. The already retained comparison helper permits only that exact diagnostic address to differ and verifies every other JSON value. Original auditor and output bytes remain unchanged. Earlier full `git diff --check` failed on unchanged application/log whitespace; this does not become a successful historical check by stripping raw evidence.

Same-author separate audit implementation/process is not independent human approval. Local evidence verification is distinct from current-head GitHub CI and review, which must be inspected before merging. Any later publication incident belongs in #34/the evidence PR, not a wrapper-only research chain.

## Integration decision

This supplies a bounded native-application saved-document part of #34: report required effect and preserved properties independently, and keep missing/mismatched evidence UNKNOWN. It does not exercise the public Agent Interface entry path, establish model-visible usefulness or complete the full Inkscape/Calc acceptance matrix. Keep #34, #57, #2789 and the repository-wide roadmap open. Runtime adoption requires a separately reviewed, current-path composition and relevant live/model evaluation.
