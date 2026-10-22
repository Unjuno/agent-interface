# V39 adapter-linked admission receipt integration A24

## Red-Green sequence

- A22 RED control: unchanged current-main V39 backend and owner emitted separate admission/release events; the retained-input analyzer rejected them because the release did not link an admission (`unmatched_admission_count=1`, one invalid release).
- A23 intermediate repair: retain and identity/time validate the exact backend-emitted admission, attach it to the release. The analyzer still rejected because its nested receipt contract requires explicit `operation="down"`, though the admission event type already unambiguously identifies that operation. A23 remains preserved as FAIL.
- A24 adds that canonical operation field to the linked copy only after the source event, key, owner, token, deadline and timestamp checks pass. It does not alter the original emitted admission or infer any server/physical state.

**PASS_METHOD_SCOPED** requires matching actual Xvfb KeyPress/KeyRelease and keymap down/up, validated joined owner-bound admission, V4 batch release verification, unchanged analyzer ready with one hold and zero malformed/unmatched/invalid counts, verified owner cleanup and stop, exact source audit, and clean WSLc cleanup. Candidate invocation once; no retry.

## Scope/source

Only the experimental copy of the current-main V39 backend adapter is changed; it retains exact admission data and validates the link before adding operation semantics. Owner V4/V12 is the A09 current-main freeze. Analyzer is current PR #8857 head `cd766747abb4ca6d321b626c0a7b9734b9e06816`. See manifest for base blob and file hashes. WSLc 3.0.1.0, immutable cached Python/Xvfb image, offline, one CPU, source read-only and output separate. No task/application/game effect or live allocation is claimed.
