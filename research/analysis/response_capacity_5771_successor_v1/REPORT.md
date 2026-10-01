# Issue #5771 successor — available adaptive response capacity

## H/T/D/C/U

- **H:** A nominal response repertoire can overstate coverage when simultaneous demand, a shared busy interval, an expired authority lease, or an unaccepted human handoff makes an otherwise known response unavailable. A state-conditioned ledger should detect the false coverage while preserving the genuinely available spare-capacity control. A reserved release lane may preserve safety without restoring task progress.
- **T:** Four deterministic synthetic scenarios crossed with three arms (nominal repertoire, capacity-aware, reserved safety lane), 12 rows total. The candidate emits raw state facts and classifications; the separate auditor recomputes from fixed scenario truth without importing the candidate.
- **D:** `PASS_METHOD_SCOPED` only when all frozen rows/facts/outcomes agree, nominal shared-saturation is falsely covered, capacity-aware shared-saturation is not covered, spare capacity remains covered, and no authority effect is applied.
- **C:** Hand-authored finite state machine, availability inputs and outcome oracle. CPython 3.12.10; construction tests 4/4 and `py_compile` passed before freeze. Docker Desktop did not respond; no container was used.
- **U:** No live contention, queue, lease, human recipient, GUI, model, production recovery, Ashby theorem, or real task-success evidence. A synthetic `COVERED` label means only within the stipulated finite fixture.

## Result

`PASS_METHOD_SCOPED`. Candidate: one CLI invocation, exit 0, 12 rows. Independent raw-only auditor: one invocation, exit 0, 12/12, zero errors. It detects nominal false coverage in shared saturation while the capacity-aware spare-capacity control remains covered. The reserved safety lane covers release in the saturated case but does not restore threat/replan coverage; safe release and task progress are distinct.

The same nominal-vs-capacity distinction also exposes the authored expired-lease and offered-but-unaccepted-handoff cases. All rows mark `authority_effect_applied=false`. No existing live evidence was regraded.

## Reproduction

From this directory run `python candidate.py`, then `python audit.py`; the auditor reads `candidate.raw.json` from the current directory. Four pre-freeze construction tests are in `test_candidate.py`. `FREEZE.json` records source hashes, allocation identity and decision gates. The Git-blob SHA256 manifest is `SHA256SUMS`.
