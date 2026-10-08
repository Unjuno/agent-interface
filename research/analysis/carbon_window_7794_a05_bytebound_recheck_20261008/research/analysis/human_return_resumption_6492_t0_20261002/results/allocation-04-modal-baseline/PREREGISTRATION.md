# Issue #6492 — immediate-modal baseline successor T0

## Relationship to parallel work

Open PR #6499 already reports a six-case × three-arm synthetic T0 for
`timing_only`, `preserved_view`, and `optional_cue`. Do not rerun or re-report
those 18 rows. The Issue's proposed comparison additionally names an
`immediate_modal` baseline; that arm is absent from the PR #6499 preregistration
and output. This additive successor tests only the six immediate-modal records
from the same frozen matched fixture. It does not modify or depend on the
parallel branch or path.

## H / T / D / C / U

**H.** The missing immediate-modal baseline can be represented for the same
six synthetic tasks and interruption questions without changing answer facts,
capturing/copying underlying content, hiding an external state-change warning,
authorizing return actions, leaking the independently authored correct return
action, or delaying urgent release.

**T.** Candidate emits only the six `immediate_modal` rows from the exact
24-row frozen fixture. An independent raw-only auditor reconstructs these six
rows and confirms complete matched-case consistency in the fixture. Within the
single audit invocation, seven corruptions test state warning removal, delayed
urgent delivery, changed question content, changed answer choices, swapped
active task, leaked correct-return action, and realized automatic effect. Candidate and auditor run once each in
separate, network-disabled OrbStack containers; zero retries.

**D.** `PASS_METHOD_SCOPED` only if all six baseline rows independently
reconstruct in exact order, the underlying view is represented without a
snapshot/copy, question/answer content equals the matched fixture, state-change
warnings remain explicit, no cue or return authority is introduced, the correct
return action is not disclosed, automatic effects remain false, and all seven
mutation controls are rejected. Otherwise `FAIL_METHOD` or `HOLD_INTEGRITY`.

**C.** The synthetic modal overlay does not model actual application focus,
interrupt delivery, human comprehension, accessibility, task resumption or
timing. Keeping the underlying synthetic view available may not correspond to
any real application.

**U.** No people, human outcomes, GUI, private screen, model, actual interrupt,
real effect, policy benefit, usability or product behavior. The six authored
rows do not establish causal effects. T1 remains separately gated by consent,
privacy and accessibility review.

## Frozen run contract

- Source base and branch HEAD at freeze: `a7817597b8405f9b7581820fe79c9242a5f65255`.
- Fixture source: root `fixture.json`, SHA-256
  `f2dc10f43fa5f5486150b101213ef1b99e359050900eee92b3786f77b1cea96d`.
- Formal outputs are unique under this allocation directory. Candidate=1,
  independent auditor=1, retries=0. Existing output path, hash mismatch, issue
  closure/result change, new same-arm allocation, or overlapping source/main
  change stops before candidate.
- Reconcile latest main before launch. Disjoint advances may be fast-forwarded
  only after verifying changed paths exclude this package, `README.md`,
  `docs/CURRENT_GOAL.md`, `ROADMAP.md`, `docs/IDEAS_AND_OUTCOMES.md`,
  `docs/RESEARCH_ISSUE_INDEX.md`, `docs/ISSUE_FAILURE_CLASSIFICATION.md`,
  `docs/WORKER_QUICKSTART.md`, and `research/analysis/README.md`. Record the
  exact live main SHA and path list. Recheck Issue #6492 and PR #6499 status.
- Cached image `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`
  (`linux/arm64`); OrbStack Engine 29.4.0; network none; separate ephemeral
  containers; read-only root/source; output-only RW mount; requested 1 CPU,
  512 MiB, pids 64, user 501:20; no GPU. Limits are requests, not verified
  enforcement.
