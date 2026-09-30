# Issue #5315 — calibration-byte binding successor T0

This is a new, additive successor allocation after v1's post-hoc digest
mutation was accepted. It does not alter v1 source, formal output, or audit
history. The question is deliberately narrower than all of Issue #5315.

## H / T / D / C / U

**H.** A certificate checker that validates the exact digest of retained
synthetic calibration bytes and recomputes summary statistics will reject
changed bytes, changed digest, changed counts, mismatched population/version,
stale input, and unsupported conditional scope. Even if it passes these
integrity checks, CRC_MARGINAL cannot certify conditional selective risk and
cannot authorize external effects.

**T.** Use one fixed 199-row binary calibration corpus (8 errors, 191 correct)
with a SHA-256 over the exact retained file bytes. Run five deterministic task
arms from v1 and six negative controls, including the v1 counterexample: replace
the digest with another non-empty string. A raw-only audit independently
recomputes the file digest, row counts, CRC arithmetic, and expected decisions.

**D.** PASS this scoped successor only if (1) exact corpus bytes/digest and
derived counts agree; (2) all six negative controls reject; (3) IID marginal
expression is 0.045 <= alpha 0.05 while selected singleton conditional risk is
1.0 and no conditional certificate is emitted; (4) shift arms fail closed;
(5) zero authority is granted. Any disagreement is FAIL; missing source or
unbound digest is HOLD.

**C.** Standard-library-only finite Python; one small fixture, no stochastic
sampling. Container remains unavailable without shared CPU-slot arbitration
under #5085, so host-only execution is explicitly not Docker validation.

**U.** This checks integrity of a synthetic 199-row fixture, not source
authentication/signature, representative-data exchangeability, deployment
shift detection, SCRC implementation, task correctness, external effect, or
runtime safety. A content hash cannot establish who created the bytes or that
the declared population matches reality.

## Freeze

Issue: https://github.com/Unjuno/agent-interface/issues/5315
Primary sources: CRC https://arxiv.org/abs/2208.02814; SCRC
https://arxiv.org/abs/2512.12844. Frozen source/base identities are recorded in
`FREEZE.json` after source commit and before the single formal invocation.
The calibration rows are explicit synthetic fixtures, not collected tasks.

## Non-authority

PASS means only that this finite checker enforces the stated byte/count/scope
contract on the fixture. It is neither production certificate validation nor
proof of task success or permission to act. Set-valued output remains a
descriptive fallback.
