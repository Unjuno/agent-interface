# #4953 copied-evidence audit-integrity probe

## H — hypothesis

The published #4733 raw-only auditor may return `PASS_DRIFT_BOUNDARY_MAPPED`
with no errors after a retained row weight is changed to JSON NaN, or after
`development_alpha` / `truth_state_count` are changed, because those fields are
not bound to independently frozen metadata.

## T — one-shot test

Use the exact current-main #4733 auditor source and the exact `RAW.json` member
from its published `RAW_AND_AUDIT.zip.base64`. The base64 file contains CRLF
line endings; remove ASCII whitespace before strict base64 decoding. Verify
source Git blob, transport Git blob, source SHA-256, and raw member SHA-256
before invoking the auditor. Keep raw bytes immutable and make three independent
deep copies: first row's `weight = NaN`, top-level `development_alpha = 0.5`,
and `truth_state_count = 99`. Run baseline and all copies through the unchanged
source auditor once in a pinned, network-disabled, read-only Docker container.
Retain results and hashes only; do not write a mutated raw artifact.

### Provenance correction

The issue body's original `c1a225…` / 12,160-byte pin refers to a different
#4912 artifact and is not used. Correct #4733 archive member:

- source commit at execution base: `081403e352aa79a6ff0cd030fbb9d2fbbf28c7e6`
- audit source Git blob: `1a6cc0e46b32d4cd6989aed118d003cce4cfe399`
- archive transport Git blob: `c38dd2002f201d49b6fc261caff019550a4bf4bc`
- raw member: 186,739 bytes, SHA-256
  `5f48e0274f9fd800ac26af3dd70bd52171700b32ce159f3cdbe0f28c7ec35e7d`
- raw state space: 21 distributions × 16 truth rows = 336.

This correction binds the intended #4733 input only; hypothesis, mutations,
decision rule, and scope are unchanged. GitHub correction comment:
https://github.com/Unjuno/agent-interface/issues/4953#issuecomment-5858088457

## D — decision

- `PASS_AUDIT_GAP_REPRODUCED`: provenance verifies, baseline emits the published
  PASS, and at least one mutation also emits that PASS with `errors=[]`.
- `FAIL_GAP_NOT_REPRODUCED`: provenance and baseline pass, and all three
  mutations fail closed.
- `STOP_PROVENANCE_OR_RUNTIME`: any identity mismatch, baseline failure, or
  execution-boundary violation. A STOP is not a scientific conclusion.

## C — controls

Original archive and extracted raw remain read-only. Each mutation starts from
an independent deep copy. Recompute the original raw SHA-256 before and after
the run. Test the unchanged published auditor rather than a rewritten helper.
The one runner invocation is distinct from the independent read-only output
auditor; no rerun, model/GPU work, or threshold change.

## U — limits

Three copied-evidence mutations in one synthetic 336-row artifact and one
auditor revision only. No reinterpretation of the unchanged-byte #4733 result,
predicate-order quality, runtime latency, arbitrary corruption coverage, or
general security certification.
