# Issue #6405 T0 result — scoped contract pass

## Result

Disposition: **`PASS_METHOD_SCOPED`**. One formal candidate completed (exit 0)
and one separate raw-only auditor completed (exit 0). The auditor reconstructed
all 5 requests across 3 display arms with zero baseline errors and rejected
all 6 frozen corruption controls.

The changed-field arm highlighted `recipient,effect` for the rare external-send
request and `scope` for the late scope change; it retained all required fields
in every arm. The bounded batch grouped only the two nonconsequential label
requests; each consequential request remained separate. Reusing r1's receipt
against changed r3 was refused as `REFUSE_DIGEST_MISMATCH`. Deny and cancel
remained distinct. Exact rows and audit are in `results/formal-01/`.

## H / T / D / C / U

- **H:** A finite renderer can keep equal request truth and exact request
  binding across static, changed-field-salience and narrowly eligible batching
  presentations. Human discrimination remains unknown.
- **T:** One frozen five-request synthetic sequence; candidate once, then a
  separately authored independent auditor once; no retries, participants,
  live approvals, provider/model, GUI, or external effects.
- **D:** All 7 frozen outcome gates in [`FREEZE.md`](FREEZE.md) passed. All
  six corruptions were rejected: omitted recipient, swapped recipient, stale
  highlight, consequential overbroad batch, stale receipt reuse, and erased
  deny/cancel response.
- **C:** This is finite authored fixture-method evidence. Candidate and auditor
  share the published contract and fixture but do not share implementation.
  The construction suite is 8/8. Formal candidate/audit outputs and command
  receipts are SHA-bound in `RUN.md` and `SHA256SUMS`.
- **U:** No habituation, attention, comprehension, false-approve/deny, burden,
  human behavior, trusted UI authenticity, broker implementation, real
  authorization or security outcome. No approval-batching recommendation.

## Execution boundary

Ran on macOS arm64 / CPython 3.14.5, not WSLc or Docker. `wslc.exe` is absent in
this task environment and an unrelated OrbStack container was already running;
the finite offline fixture has no container-dependent semantics. This is a
disclosed host-only deviation from the repository's WSLc preference, not
container/resource-enforcement evidence.

## Follow-up

Keep #6405 open. T1 requires separate voluntary consent, privacy/accessibility
review, and prospective randomized/counterbalanced non-sensitive vignettes
with human comprehension plus choice endpoints. This T0 does not authorize or
justify that study by itself.
