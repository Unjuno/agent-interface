# Counterexample-qualified guard refinement — T0 construction report

## Disposition

**Host construction audit: `PASS_METHOD_SCOPED`. Formal WSLc T0: `HOLD_RESOURCE` (not run).** The result is limited to one deterministic, authored 11-state fixture and does not establish live interface correctness, safety, performance, or production utility.

## H / T / D / C / U

- **H:** In a finite declared observation vocabulary, replay-qualified counterexamples can refine a cache guard while preserving distinguishable valid controls, invalidating dependent siblings, and holding observational aliases as UNKNOWN without expanding authority or replaying task input.
- **T:** Six classified counterexample events across 11 synthetic states; compare unchanged guard, invalidate-all/fallback, exact-state blacklist, candidate refinement, and oracle-minimal diagnostic. Candidate and raw-only auditor are separate programs.
- **D:** For formal evidence, the auditor must reconstruct all candidate rows, identify zero harmful admissions, enforce UNKNOWN on aliases, check sibling invalidation and fallback authority, and reject every planted mutation. Construction tests exercise these checks but are not the formal gate.
- **C:** Exact finite predicates or invalidate-all may suffice; tied singleton refinements are both retained. The oracle-minimal arm is diagnostic only.
- **U:** Truth labels, replay independence, predicate completeness, dependency inventory, and representativeness are stipulated by the fixture. No GUI, actual cache lifecycle, task-effect, model, latency, or application transfer is tested.

## Results observed on host

- `python3 -B -m unittest discover -s . -p 'test_*.py' -v`: **13/13 PASS**.
- `python3 -B -m py_compile candidate.py auditor.py`: PASS.
- Candidate host invocation: exit 0; emitted 6 event rows and 11 state decisions.
- Separate auditor host invocation: exit 0; **`PASS_METHOD_SCOPED`, errors `[]`**; 2 incomparable refinement alternatives; both predicate-dependent sibling caches invalidated.
- Candidate arm: harmful admitted 0, harmful deopt 1, harmful unknown 4; valid admitted 2, valid deopt 0, valid unknown 3.
- Unchanged guard admitted 4 harmful states. Exact-state blacklist admitted 1 harmful state. Invalidate-all/fallback admitted 0 harmful but also 0 valid states. These are fixture counts, not population estimates.
- Candidate raw SHA-256: `fd5a802a69cf12e0e8f26591a6cf8743c25ae3b1a77f39624ec3c3859a0bde4a`.
- Host audit SHA-256: `90d0c85358cd715bcc69d3fe9027a276aa3489f5bb4cc57fcbf13d5574d9ba7c`.

Raw output and audit are under `results/construction/`; stdout captures accompany them. `RUN_RECORD.json` records counts/hashes. `RESOURCE_HOLD.md` is the controlling formal disposition. `RUN_COMMANDS.md` contains frozen WSLc plans only; no container command was launched.

## Why formal is held

This checkout runs on macOS arm64 and has no WSLc executable. The empty inventory snapshot in another owner's #6354 preflight is neither assignment nor release; #5085 requires explicit ownership/allocation and disallows self-assignment. No Docker/OrbStack substitution was attempted. Formal candidate/auditor/container invocation counts are **0/0/0**. No resource-only issue or slot request was created; independent permitted construction was completed instead.

## Interpretation

The finite method checks whether one particular counterexample set and vocabulary admit a conservative refinement. The positive audit only shows agreement between this candidate's raw outputs and a separately implemented reconstruction over the same authored fixture. It does not establish that real replays are independent, the vocabulary is complete, cache dependency metadata is sound, or a generic fallback is safe in a real application. Unknown aliases and unavailable fallback remain holds, not successes.
