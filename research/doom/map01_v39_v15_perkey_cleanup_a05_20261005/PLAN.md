# A05 — V39/V15 per-key release recovery (current-main synthetic probe)

## H — Hypothesis
On current main `f1d7dd1da44cad3e5fd22a65d7bec21d40289d1d`, the selected production V39/V15 release backend composed with transition-owner V4/V3 and owner V12 detects one injected dropped KeyRelease through a fake server keymap sample, retries, and reaches a neutral fake-server state before ExecutorV13 publishes a completed terminal. The measured outcome is synthetic server-state bookkeeping only.

## T — Test
One frozen candidate invocation in the pinned Python 3.12.15 amd64 image runs two ordered arms in one process: normal release, then one injected dropped KeyRelease. Both use identical one-step F8 down/up actions, fake Xlib/display/keymap, production selected release-composition code and production V12 owner code; only the base controller action-loop/session seam is a test double. Auditor independently checks raw claims/schema, terminal and event invariants, attempt receipts/timestamps, and all 21 pinned source snapshots/materialized files. No retry of candidate or auditor after execution begins; retain any STOP/FAIL raw and diagnose without relabeling or rerunning.

## D — Decision
PASS only if both terminals complete, both fake servers are neutral after executor release, each case has one owner-transition release row marked verified with physical authority false, normal uses one successful attempt, loss arm records first attempt still down then a second attempt neutral, and source/raw hashes audit cleanly. FAIL if injected loss remains down or reports successful terminal without neutral state. STOP if setup fails before both cases execute. Audit failure is preserved as audit failure and does not authorize candidate rerun.

## C — Alternatives and confounds
A retry may appear successful because the fake server implements synchronous deterministic state updates unlike X11; owner bookkeeping or cleanup may be more permissive than real transport. Ordered paired arms share one process, imports, and clock; there is no randomized order or independent process replication. Candidate's test-double action loop excludes the full ViZDoom/game stack. A single dropped event does not characterize repeated loss, real transport faults, or external consumers.

## U — Limits
This is one construction experiment with two synthetic arms, not a statistical sample. It cannot establish X11 delivery, GUI/game behavior, physical keyboard release, application consumption/effect, useful feedback, MAP01 progress, recovery efficacy, latency, threat resistance, or production safety. The fake server's own state is the only release oracle.
