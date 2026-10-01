# Issue #5550 T0 — maximally permissive supervisor under uncontrollable events

**Disposition: `PASS_T0_SYNTHETIC_SCOPE`.** In the declared, fully observed finite DFA, fixed-point synthesis admitted safe completion after recoverable focus loss and target change, while excluding stale-target commit and duplicate effect. The independently enumerated maximal policy matched. This is a model-level result only; no live interface or general transfer claim follows.

## H / T / D / C / U

- **H:** A computed supremal safe, nonblocking supervisor admits more safe completions than the frozen fail-closed comparator, never admitting stale commit or duplicate effect; a greedy allow-list exposes both hazards.
- **T:** Depth-5 exhaustive trace exploration of a frozen finite plant under fail-closed, greedy allow-list, and fixed-point synthesized policies. One candidate run in a network-disabled OrbStack container, followed by one raw-only audit in a separate container. The audit independently brute-force enumerated every subset of controllable plant edges and checked safety/nonblockingness.
- **D:** PASS only if the raw-only replay and exhaustive policy enumeration agree, audit errors are empty, synthesized unsafe transitions are zero, synthesized successful completion count exceeds fail-closed, and greedy exposes stale-commit and duplicate-effect counterexamples. All gates passed. This applies only to the frozen DFA.
- **C:** Conservative fail-closed may still be preferable for partially observed real interfaces; observed progress can be entirely due to the declared recovery transitions rather than a practical synthesis advantage.
- **U:** Synthetic, fully observed, finite plant; hand-authored state/event abstraction. No GUI, image/event classification, timing, hidden effects, utility, fairness, real supervisor integration, or proof for unmodeled states/events.

## Experiment and audit outcome

The plant has 13 transitions, three controllable event types (`ACT`, `COMMIT`, `REACQUIRE`), three uncontrollable event types (`FOCUS_LOST`, `TARGET_CHANGED`, `WINDOW_CLOSE`), a depth bound of 5, and two unsafe terminals (commit while stale; second effect after commit). The candidate computes the winning region by iterating uncontrollable safety closure and coaccessibility, then enables every controllable edge internal to that region.

| Policy | Explored transitions | Completed traces | Uncontrollable blocks | Unsafe transitions |
|---|---:|---:|---:|---:|
| Fail-closed | 10 | 1 | 5 | 0 |
| Greedy allow-list | 51 | 4 | 17 | 4 |
| Synthesized | 47 | 4 | 17 | 0 |

The independent auditor checked 108 raw rows, enumerated all 64 subsets of the six controllable plant edges, found 44 safe/nonblocking supervisors, and confirmed the candidate edge set equals the union (maximal permissive policy) of those valid supervisors. The auditor returned `PASS_T0_SYNTHETIC_SCOPE`, `errors=[]`; `unsafe_synthesized=0`, `unsafe_greedy=4`, `completed_synthesized=4`, `completed_fail_closed=1`.

Synthesized enabled edges were `READY:ACT`, `ACTED:COMMIT`, `FOCUS_LOST:REACQUIRE`, `STALE:REACQUIRE`. All other controllable edges were disabled. `WINDOW_CLOSE` remained uncontrollable and led to the explicit blocked terminal where recovery was impossible.

## Formal execution provenance

- Allocation: `MAXPERM-SUPERVISOR-5550-T0-ORBSTACK-20260930-02`, authorized by the direct user instruction recorded on coordination Issue #5085; bounded window recorded there.
- Frozen main: `716f8864948023abb3f70f60a5053c66ec4c2737`; preregistration commit: `d73031fb3790b43b1b6afdf96c68b05e2eaf4353`.
- OrbStack context; exact image `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`, `linux/arm64`, Python 3.12.14. Image config had no Entrypoint and default Cmd `python3`; both invocations explicitly used `--entrypoint python3`.
- Candidate and auditor each ran once in separate containers; network disabled; read-only root and source; caps dropped; `no-new-privileges`; 1 CPU; candidate 512 MiB, audit 256 MiB; 64 PIDs.
- Candidate exit 0; raw SHA-256 `f17273be18b33083353a883c47c2834a3c33457cb4daada2227aeaf00bd6eb8b`.
- Independent audit exit 0; output SHA-256 `594e785a1a607c7bdab636e3687201fc225d0e0075ca0eec1be6423db60aad2d`.
- Frozen source hashes are in `FREEZE.json`; exact invocations and post-run container inventory are in `RUN_LOG.md`.

## Validation and boundaries

- Local CPython construction suite: 7/7 passed; `py_compile` passed.
- `python3 research/analysis/check_index.py`: passed after generated index refresh.
- `git diff --check`: passed.
- The original formally observed raw and audit outputs are retained unchanged. No retry, image pull/build, model/GPU/GUI action, network access, or external effect occurred.
- This does not establish maximal permissiveness under partial observation, physical GUI safety, progress probability, latency benefit, fairness, or correctness of the state abstraction. Issue #5550 remains a research question beyond this first-unit finite-DFA test.
