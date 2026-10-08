# Issue #6492 T0 preregistration

## H / T / D / C / U

**H.** For a bounded, non-sensitive interruption fixture, source-bound return
context plus an optional user-authored prospective cue can be represented
without changing task facts/answer access, exposing private content, turning a
cue into authority, suppressing state-change warnings, or delaying urgent
release. T0 tests whether the evaluation contract can represent and audit those
conditions; it does not test human benefit.

**T.** Freeze six authored scenarios, each crossed with four assigned
presentation arms (immediate modal, timing-only, preserved view, preserved
view plus optional cue): 24 rows total. Keep task facts, pending step,
independently authored correct return action, interruption question, answer
choices/facts, warning interval, question duration, changed-state condition,
and source identity identical within each matched scenario. The cue offer is
the only intentional cue-policy contrast. Include cue uptake and non-uptake,
changed app state, a simple no-cue case, duplicate-effect risk, and urgent
release. Run one deterministic candidate and one independent raw-fixture audit
in separate, network-disabled OrbStack containers. Six frozen output
corruptions cover swapped task/window, stale cue after external edit,
agent-authored cue, duplicate save, absent offered cue, and delayed emergency
release. No people, GUI, model, private files, or real effects.

**D.** `PASS_METHOD_SCOPED` only if the independent auditor reconstructs all 24
rows in order; confirms all six complete matched sets and invariant task,
question, answer, state and source-view fields; and rejects all six corruption
controls. Otherwise `FAIL_METHOD` or `HOLD_INTEGRITY`. This does not estimate
return accuracy, resumption time, cue uptake, user burden, or an interruption
policy effect.

**C.** The chosen synthetic arms and deterministic rendering may omit real
attention, comprehension, accessibility, app-specific cues, and timing
interactions. A preserved view may add no value when normal application state
already supports return. Cue affordance itself may add burden.

**U.** No participants, consent, human task, personal desktop, GUI, model,
actual interrupt delivery, or app effect is tested. The external cognitive
literature motivates the hypothesis but supplies no effect estimate for this
interface. Any human T1 requires separate voluntary consent, privacy and
accessibility review and independent outcome truth. The 24 rows are authored
fixture cases, not samples of users or prevalence.

## Frozen contract

- Source base: `df2e5c6f3ca7288f5a054195f8a746d1ab4ead54` (`main` at the final pre-allocation refresh; the worktree was fast-forwarded before freeze).
- Issue: #6492, open, unassigned, no comments at intake; targeted PR/branch
  searches found no named competing T0 allocation.
- Fixture generator and exact generated `fixture.json` are included in the
  source manifest. Six scenarios × four arms; no generated/hidden data.
- Candidate `candidate.py` reads only the fixture and emits presentation
  records. The auditor `audit.py` independently derives records from raw
  fixture fields and does not import candidate code.
- Construction tests are separate from candidate and auditor invocations.
- Image: cached `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`,
  `linux/arm64`; OrbStack Docker Engine 29.4.0. Each formal process runs once
  in its own ephemeral container, network disabled, source read-only, output
  mounted separately, one CPU, requested 512 MiB memory, pids limit 64, user
  501:20, read-only container root. No GPU.
- Maximum formal candidate=1, auditor=1, retries=0. Any post-freeze change,
  missing output, nonzero exit, main advance before start, or source/image
  mismatch terminates this allocation. Preserve the first outcome.

## Interpretive boundary

This T0 validates a synthetic protocol/evaluator only. A pass cannot be
described as evidence that a source-bound view or cue improves correct human
return, time, effort, safety, or task performance.
