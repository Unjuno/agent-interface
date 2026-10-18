# Issue #8135 T0 A02 — persistent-counterparty method result

**Disposition: `METHOD_PASS_SCOPED`.** In the frozen finite simulator, a
history-responsive persistent learner changed its later-episode UI variant
conditional on a public route event, while a fresh-reset control and a
frequency-matched, history-independent sham did not reproduce that conditional
profile. The offline hard gate admitted the authorized positive control and
zero unauthorized add-on effects. This validates only this hand-authored
method fixture; it does not show that real services persist or adapt to agents.

## H / T / D / C / U

- **H:** A persistent history-responsive counterparty changes later-episode
  variant selection relative to both fresh-reset and frequency-matched
  history-independent controls, and this profile difference remains visible
  in route-level proposals/abstentions under a fixed admission rule.
- **T:** Fresh schedule seed `20261006`; 40 blocks / 80 episodes across five
  arms, two routes, two public histories, balanced route order, and two sham
  assignment slots. Candidate received only the public schedule; sealed effect
  truth was mounted only for the separate raw-only auditor.
- **D:** Auditor reconstructed all 80 episodes, all 40 blocks, route counts
  40/40, state/reset assignments, and the outcome oracle. The learner's later
  profile was H_FAST → 4/4 add-on vs fresh-reset 0/4 and sham 2/4; H_CHECKED →
  0/4 add-on vs sham 2/4. Persistent learner and sham each had 8/16 add-on
  presentations overall. Stationary and persistent-null arms made no switch.
  The fixed gate accepted 64 authorized positive effects and zero unauthorized
  effects (6 unauthorized proposals blocked; 10 add-on abstentions). All 5/5
  future/private-leak, omission, route-order, and sham-history mutations were
  rejected.
- **C:** Every schedule, selector and route is deterministic and authored; the
  same aggregate exposure frequency can conceal different conditional profiles.
  A correct audit of this finite fixture does not validate the fixture as a
  model of real interfaces.
- **U:** No model, browser, GUI, service, credentials, human, actual task, live
  effect, latency, deployment prevalence, production adversary or safety claim.
  T1 remains separately gated and is not authorized by this result.

## Execution provenance

- Allocation: `UNJUNO-8135-T0-A02-ORBSTACK-20261005`.
- Main base: `b6907899f11b036f2af572e8d4794ebb4b7e5c83`.
- Image: `python@sha256:c3e521df8b2b498a7a682e7e18676771cb80c6b75b8699af886b2d554ce40151`
  (`linux/arm64`, cached; no pull); OrbStack Docker, network disabled,
  read-only rootfs, one CPU requested, memory enforcement not asserted.
- Candidate 1/1 exit 0; auditor 1/1 exit 0; retries 0. Candidate output SHA-256
  `7f8e3ca23370ebe6c71dee7538e47f5883e56810d5cd2992f77589b8f7921a2e`;
  audit output SHA-256
  `63b83f05b53acb27c38153ade3674c0a8e686c1d5b0cd9b27a9692239d872b56`.
- Full commands, frame-independent inputs, source hashes and raw results are
  retained in this directory and `SHA256SUMS.txt`.
- `FROZEN.json` has a branch-label typo (A02 recorded, A01 was the actual
  checked branch). The exact-base evidence is intact; see
  `PROVENANCE_CORRECTION.md`. Frozen bytes are not rewritten.

## Predecessor

A01 is preserved unchanged as `FAIL_INTEGRITY_AUDITOR_EXPECTED_SCHEMA`: its
single candidate emitted 80 rows; its single auditor invocation rejected the
generated episode schema because the auditor's expected field set omitted
`arm`. Candidate/auditor/retries were 1/1/0. A02 is a separately frozen fresh
schedule seed with that contract corrected; A01 is not replayed.
