# A09 pre-registration — test V15 key-up retry after complete fixture binding

Issue: [#59](https://github.com/Unjuno/agent-interface/issues/59), the current-main V39/V15 per-key release measurement path.

## H/T/D/C/U

**H — Hypothesis.** A07 stopped because its test-only `ControllerBackend.execute` omitted the focus lease binding and `(intent, step)` input-event context that the production session supplies. With both fields derived from the stable fake focus observation, unchanged V13/V15/V4/V3/V12 production code will retry one dropped first KeyRelease and end with an empty fake-server keymap before terminal publication.

**T — Minimum test.** Execute the newly identified A09 candidate exactly once against the 21-file Git-blob-pinned source closure from current main `712a71b25dc024b5406b24b568225c0663e7278b`. It runs a positive control with no injected loss, then a treatment dropping only the first fake KeyRelease. Before the run, a no-input import preflight must load `ExecutorV13` and the V39 batch backend. The treatment candidate must report both release rows and normal terminal receipts. An independent auditor will examine only the retained raw JSON and source manifest.

**D — Decision.** `PASS_CONSTRUCTION_SCOPED` requires: both arms complete exactly one step and terminal with verified empty release; control has exactly one server key-up attempt with before=true/after=false; treatment has exactly two attempts, first after=true and second before=true/after=false; exactly one fake KeyRelease was dropped; and both final keymaps are empty. Missing prerequisite/imports is STOP before treatment. An executed treatment that misses any condition is FAIL. No retry after candidate invocation.

**C — Competing explanation.** The key-up retry may depend on fake-X's synchronous state update and not transfer to X11 timing. A07's STOP was a harness omission and says nothing about retry behavior. The expected result can validate only the selected software composition under synthetic focus and server state.

**U — Uncertainty.** No real X11 server, GUI, physical keyboard, Doom, game time, model, task effect, independently useful feedback, survival, latency distribution, or live threat exposure is exercised. The private game allocation remains unassigned and untouched.

## Freeze

- Candidate identifier: `a09-current-main-712a71b-20261005-one-shot`.
- Base SHA: `712a71b25dc024b5406b24b568225c0663e7278b`.
- Production source files: 21 files; exact Git blob IDs and SHA-256 values in `source-manifest.json`.
- Candidate source SHA-256 and freeze time: `FREEZE.json`.
- Inputs: fixed normal F8 DOWN/UP, then fixed one-drop F8 DOWN/UP; both in one candidate invocation.
- Execution: Codex bundled Python 3.12.14, Pillow 12.3.0, macOS host. The required sparse directories are now present; no live services or GUI are used.
- Container: OrbStack image preflight failed with `operation not supported`; recorded at A08. This run is host-only and does not claim a container execution.
- Retention: candidate writes `results/candidate.json` once. Auditor reads that file, never regenerates or modifies it.
- A07 remains immutable evidence of its pre-treatment STOP. A08 remains immutable evidence of sparse-source setup STOP. A09 is the only candidate execution under this plan.
