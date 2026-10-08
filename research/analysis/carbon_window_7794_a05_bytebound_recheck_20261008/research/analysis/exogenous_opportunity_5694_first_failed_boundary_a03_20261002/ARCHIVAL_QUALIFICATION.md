# Recovery of closed PR #6799: preserve the scientific HOLD

Source tip: `c5efbf4d264403b4936c468299b81d9d3243fbd5`, formerly remote
`research/exogenous-opportunity-5694-first-failed-boundary-a03-20261002`.
All twenty original evidence/source files, including `SHA256SUMS`, are copied
byte-for-byte. The source branch actually placed them at the repository root
(`execution/formal-01/` for outputs), despite its freeze and PR naming this
analysis directory as the intended artifact path. Recovery relocates only
those files to that declared additive path; main's root README/REPORT and
other existing root files are not overwritten. The original paths remain
recoverable in the complete source commit through its archival tag.

## Gate and disposition must not be conflated

The original native-Windows CPU run record reports one candidate and one
independent auditor invocation, both exit 0, zero retries, nine replayed rows,
and five corruption controls counted. The audit receipt says
`PASS_METHOD_SCOPED`, but scientific disposition remains
`HOLD_PHASE_CONTRAST_NOT_MATCHED`. The hit arm uses capture times `[10]` and
horizon 50 ms; the miss arm uses `[10, 50]` and horizon 60 ms. This violates the
preregistered common-capture-schedule phase-only contrast. The different
classifications are descriptive, not causal support for the hypothesis.

The retained auditor's corruption-control calculation checks that each
mutation differs from its independently reconstructed expected rows; it does
not run every mutation through a separate acceptance API. Recovery does not
upgrade that historical control count to broader robustness or live-system
validation. No GUI, safety, human-tempo, product or performance result follows.
No predecessor output or Issue #5694 status is changed.

## Recovery checks

All nineteen original SHA-256 manifest entries verify at the relocated path.
The eight unchanged construction tests pass locally. Added read-only archival
tests check the manifest, nine stored rows against the retained independent
replay function, and the exact capture/horizon mismatch supporting the HOLD.
They do not call a formal main/wrapper, write original outputs, or re-execute
the consumed Windows allocation. Local Python/macOS checks do not attest the
original host/runtime or rerun its formal commands.

The initial whitespace gate flagged one original Markdown hard break and four
Windows CRLF evidence lines. Those source bytes are retained rather than
normalized. The recovery edits are checked separately, allowing CR-at-EOL and
excluding only the unchanged original REPORT. Package-local `-text` attributes
protect the preserved hashes from checkout/add newline conversion.
