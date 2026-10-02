# Issue #5836 successor T0 — corrected stateful single-use semantics

Allocation: `trusted-confirmation-5836-t0-successor-20261001-01`  
Base main: `45395880f873f1592bc188a37471d8380535e1ec` (freshly observed at freeze)  
Additive path: `research/security/trusted_confirmation_5836_t0_successor_20261001/`

This is a new source and decision allocation, not a rerun or overwrite of allocation `trusted-confirmation-5836-t0-20261001-01`. The prior raw and invalid-oracle stdout remain unchanged.

## H/T/D/C/U

- **H:** A broker with an independent confirmation issuer, exact principal/request binding, revocation/expiry checks, and a nonce consumed before first attempt rejects forged, substituted, revoked, stale, replayed, and lost-response retrial cases while allowing one exact matched approval and explicit denial.
- **T:** One deterministic 10-row finite fixture. Compare page/model-text approval, a request-bound but replayable receipt, and trusted single-use receipt semantics. Include a replay whose nonce is already marked consumed before this observed request, target/principal substitution, revocation, expiry, lost response, valid matched grant and denial. Run candidate once and an independently authored raw-only auditor once in pinned local Docker; network none, read-only source/root, bounded CPU/memory/PIDs.
- **D:** PASS only if every row matches the auditor, trusted effects occur only once for `valid_match`, lost response consumes its nonce without retry, replay/substitution/revocation/expiry refuse, weaker arms reveal page-forgery and replay failure, and five mutations reject. Else retain FAIL/STOP; no rerun.
- **C:** An out-of-band broker boolean plus an effect digest could be simpler; capability/lease validation may already enforce the same constraints.
- **U:** Synthetic provenance is not a real trusted UI/channel, nor human comprehension, accessibility, coercion resistance, or application effect evidence.

Local main was rechecked immediately before this freeze; container commands and source/image hashes will be retained with the result. No hosted workflow is used.
