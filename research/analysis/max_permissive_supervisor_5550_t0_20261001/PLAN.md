# Issue #5550 T0 — uncontrollable-event supervisor

## H / T / D / C / U

- **H:** For the declared finite plant and safety specification, a computed supremal safe, nonblocking supervisor admits safe completion after recoverable focus-loss and target-change events, while never admitting stale-target commit or duplicate effect. It should admit more successful completion traces than the fail-closed baseline; a greedy allow-list should expose both counterexamples.
- **T:** Candidate computes the safe controllable region and coaccessibility fixed point, enabling all controllable transitions that remain in the supremal winning set. Independently, the auditor brute-force enumerates every subset of controllable plant edges, retains all safe/nonblocking supervisors, and unions their enabled edges. Exhaustively explore all plant traces through depth 5 under fail-closed, greedy allow-list, and the candidate supervisor. Run candidate once in a network-disabled OrbStack container. Only on exit 0, run the independent raw-only auditor once in a separate container. Host construction tests are not formal result.
- **D:** `PASS_T0_SYNTHETIC_SCOPE` iff raw-only independent replay has zero errors, synthesized rows contain zero unsafe transitions and at least one safe completion plus uncontrollable block, and greedy rows expose stale-commit and duplicate-effect counterexamples. A synthesized unsafe transition is FAIL. Any model/plant uncertainty or incomplete coverage is UNCERTAIN, never generalized beyond this DFA.
- **C:** Conservative fail-closed may be preferable in real partially observed interfaces; the apparent extra progress may derive entirely from the hand-specified recovery transitions rather than supervisor synthesis.
- **U:** Synthetic fully observed finite plant only. No live GUI, event classifier, asynchronous timing, hidden effects, utility/latency, fairness, or real supervisor synthesis/integration. The supervisor table is hand-specified, not inferred by a general synthesis algorithm; this probe tests its behavior against the declared plant, not algorithm completeness.

## Frozen plant and protocol

States include READY, ACTED, FOCUS_LOST, STALE, COMMITTED, an uncontrollable blocked terminal, and two unsafe terminals. Controllable events are ACT, COMMIT, REACQUIRE. Uncontrollable events are FOCUS_LOST, TARGET_CHANGED, WINDOW_CLOSE. Safety forbids COMMIT from STALE and ACT after COMMITTED. Maximum trace depth is 5. The literal transition table and fixed-point candidate are in `model.py`; the independent auditor uses a literal transition table and exhaustive controllable-edge-subset enumeration in `audit.py`, importing no candidate module.

Exactly one formal candidate invocation and, only if it exits 0, one separate raw-only audit invocation. No retry, image pull/build, network, GPU, model, GUI, or external effect. Preserve any failed formal invocation as STOP and do not rerun this allocation.

## Construction chronology (pre-freeze)

Initial construction uncovered: (1) unittest discovery from repository root did not add the fixture directory to imports; subsequent local tests run from the fixture directory; (2) a depth-4 check excluded the 5-event recover-after-focus completion; depth 5 was frozen; (3) the first greedy exploration stopped at COMMITTED and therefore omitted duplicate-effect behavior; the frozen candidate now continues only that greedy arm past COMMITTED to expose the defined duplicate transition; (4) a hand-written policy table was insufficient to test supervisor synthesis, so the candidate fixed-point algorithm and independently brute-force enumerated oracle replaced it before freeze. These are pre-freeze construction corrections, not formal results; no formal invocation occurred during construction.

## Validation commands

```sh
python3 -m unittest -v test_model.py
python3 -m py_compile model.py audit.py test_model.py
python3 ../check_index.py
git diff --check
```
