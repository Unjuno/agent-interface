# V39 bracket timestamp type-alias check — A01 (construction)

**Disposition:** PASS_BRACKET_TIMESTAMP_TYPE_VALIDATION after one narrow construction repair. The frozen PR #7662 projector incorrectly paired malformed Boolean timestamps; the candidate now rejects them while preserving the coherent positive. No runtime or live allocation was used.

## H/T/D/C/U

- **H:** The V39 per-key projector must require duplicated sampling-bracket timestamps to be exact JSON integers. A JSON true or false must not pass merely because Python considers it equal to integer 1 or 0.
- **T:** Load the exact input_edge_receipts function from the frozen #7662 base commit and candidate source. Reuse the retained positive A01 DOWN/UP event pair, coherently set DOWN interval to [0,1] and UP interval to [2,3] while updating samples/request/ack/brackets, then mutate only the duplicated DOWN bracket lower endpoint to false and upper endpoint to true. The positive control must remain paired. Both malformed rows must be incomplete with null intervals. Run once before and after a narrow type-validation repair; retain the initial outcome.
- **D:** Baseline reproduction occurs if the coherent positive is paired and both bool-alias rows are also paired. The candidate passes only if the positive remains paired and both bool-alias rows become incomplete with both timing intervals null.
- **C:** The existing projector validates the canonical adapter interval with exact type(value) is int; exact bracket typing should match that conservative contract. This does not establish that source measurements represent physical key dwell or application consumption.
- **U:** The sample is a retained X-server keymap bracket fixture. This test concerns deterministic Python/JSON representation only; no OS, application, gameplay, latency, safety, recovery, or task-effect claim follows.

## Freeze and provenance

- Repo main at freeze: decefbd53240cdac21633e0d3e66c7e3bec76722.
- Stacked parent at initial freeze: PR #7662 head 719ef679c977a925db3a6d1fe15f9cd93cf2b42c. The branch advanced during this work; the candidate was rebased onto current PR #7662 head 1ced273cc78fde3d0d9e70a147285126bfabecb0, whose projector still had the same bracket type omission. The frozen baseline source and fixture blob remain identical.
- Exact source: research/doom/map01_overlap_controller_v39.py, Git blob 21e6b164562725dfb502d5a7a7d9ceb06fb92bd6, pre-repair SHA-256 4c54851ecfe9798c331f10a871a68fe816406b2873d5759dad7675f1d4ecc01e.
- Fixture: research/doom/v39_application_consumption_conflict_59_a01_20261005/INPUT.jsonl, Git blob eacb735634d6c6761ba7fa39448e6d7d43e342d5; byte copy INPUT.jsonl SHA-256 ad0b1c29da4b626e9be27e8716cdabfbb25ac49dcf0abd4bda4bd2f7a9f84e4e.
- Frozen runner: run_a01.py, SHA-256 a92bc8c213580662c3d254549a86c2ae357d914fabe182174c45000ee2b7ed6c. The exact frozen source snapshot is available at research/doom/v39_application_consumption_conflict_59_a01_20261005/CANDIDATE_SOURCE.py.txt and has the same Git blob as the original controller.
- Repaired source SHA-256 after rebase: 203060c23fe5ccb05655f875be2175ce2754c17e6582540d893b03158983bc7c.
- Runtime: CPython 3.11.9. The runner AST-extracts only input_edge_receipts and uses the standard library; no container or WSLc was needed for this exactly determined source/JSON property.

## Result

The first frozen runner outcome is retained in raw/A01-red.json, stdout/stderr, and exit code. It returned FAIL_TYPE_ALIAS_ACCEPTED: the positive and both single-field Boolean mutations all projected as paired with non-null intervals. The source-bound regression then reproduced two failures: false aliased integer zero and true aliased integer one.

The candidate adds one fail-closed condition in bracket_matches: the duplicate bracket interval must pass the existing exact-integer valid_interval predicate before it can match the canonical adapter interval. The candidate keeps the positive paired and rejects both mutated rows as adapter_edge_receipt_incomplete with both derived intervals null.

Validation commands and outcomes:

- py -3.11 -m unittest research.doom.test_map01_v39_bracket_time_type_alias -v — 3/3 pass.
- py -3.11 -m unittest research.doom.test_map01_v39_typed_state_feedback -v — 30/30 pass.
- Initial py -3.11 run_a01.py raw/A01-green.json — PASS_TYPE_ALIAS_REJECTED; after rebase, raw/A01-REBASED.json independently records the same pass against the current #7662 base.
- py -3.11 audit_a01_v2.py — PASS_INDEPENDENT_REPLAY, all 11 checks pass using the exact frozen commit.
- py -3.11 audit_a01_v3.py — PASS_INDEPENDENT_REPLAY, all 11 checks pass using the preserved source snapshot, so replay does not require the PR-head commit object.
- The permanent unittest reads the source snapshot from the parent evidence package; it therefore remains runnable after a squash integration.
- py -3.11 -m py_compile for the changed module, regression, frozen runner, and auditors v1/v2/v3 — pass.
- git diff --check HEAD — pass.
- SHA256SUMS — 56 listed files verified with zero mismatches by manifest-verify-v2; the manifest excludes itself and manifest-verification logs to avoid self-reference.
- The first checksum pass included its changing stdout log and found one self-reference mismatch; its exit-1 output is preserved. The corrected verifier writes to a separately retained v2 log excluded from the manifest.
- The pre-rebase green run had the right behavioral result but its hash named the earlier candidate blob. It is retained unchanged; the post-rebase green run and AUDIT-REBASED records bind the current parent source and repaired candidate.
- Initial auditor v1 failed its structural check because it searched only direct AST children for a helper nested inside a loop; raw/AUDIT.json and its command output preserve that verifier failure. Auditor v2 changes only the traversal to ast.walk; its passing output is distinct and does not overwrite v1.
- One early unittest harness attempt raised TypeError because the extracted function was bound as a test-class method. That attempt's output was overwritten during test-harness correction; the frozen runner's first fail-open result and the corrected regression's expected RED output are retained separately.

Raw outputs, exact byte fixture, frozen source identity, audit, and SHA-256 manifest are adjacent. This is deterministic projection construction evidence only; Issue #59 live threat exposure, physical key timing, useful feedback, recovery efficacy and MAP01 progress remain unverified.
