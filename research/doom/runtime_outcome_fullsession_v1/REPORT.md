# Full-session runtime outcome integration v1

Decision: **retain the reasoned provider-outcome classifier as a full-session integration candidate; retain the predeclared audit as FAILED TOOLING.** This is not a shared-runtime promotion.

Publication base: `d7d46bbababe186853da2e338f69382fa1070259`. Immutable executed runtime base: `9e6d5ecdbb5440fd5df1883161f2c63b2c3bb245`. Prefreeze GitHub receipt: `c5b996b4e0f02471f97d744e32916251e37a3036`.

## Question

Earlier real MAP01 evidence already covered restored timeout and running states. The remaining gap was whether the same `runtime_score.py` classifier preserves **true map exit** and **player death** through the complete `session -> Executor -> XTEST/InputOwner -> finish -> first score.json/post_control_score` path.

No timeout/running live cases were repeated. Two tiny authored PWADs expose exit and death deterministically. This is a scorer/runtime-contract experiment, not gameplay efficacy or a normal MAP01 clear.

## Frozen measured allocation

Six first-outcome cases, three per endpoint, order `exit/death`, `death/exit`, `exit/death`. Exact source/fixture hashes and all IDs were frozen on GitHub before the first measured case. Same-ID reruns: zero.

- exit: OS `e` hold 1000 ms, owner cutoff 1500 ms;
- death: OS `[a,d]` hold 5000 ms, owner cutoff 3075 ms; sector damage causes death during control;
- ViZDoom 1.3.0 / Freedoom IWAD / ASYNC_SPECTATOR / visible X11;
- 10 Hz owner-thread evaluator, reasoned outcome mode;
- no model calls or engine action-selection API.

## Live result

| Endpoint | First score classification | map_exit | player_dead | Program terminal | Verified release |
|---|---:|---:|---:|---:|---:|
| True exit | MAP_EXIT 3/3 | true 3/3 | false 3/3 | completed 3/3 | 3/3 |
| Death | DEAD 3/3 | false 3/3 | true 3/3 | expired 3/3 | 3/3 |

Exit wall-control duration median 1046.991 ms, range 1037.563–1047.032 ms. Death wall-control duration median 3102.498 ms, range 3101.972–3105.933 ms. These are scenario timings, not performance claims.

All six final scorer receipts agree with the first persisted score on `map_exit`, `episode_finished`, `player_dead`, `death_count`, and `kill_count`. Scorer missed periods: 0. The outcome acquisitions are honestly bracketed and bind the emitted termination kind to the sampled provider state.

The death cases expose a separate lifecycle fact: task death does not itself shorten the old owner lease, so the motor program reaches `expired`. That is not a scoring failure and is handled by separate lifecycle-invalidation research.

## Prefrozen audit failure retained

The predeclared `audit_full.py` returns **0/6 PASS**. The unique failure in every case is `driver score diverges from first score.json`.

This is an audit bug, not a live-score discrepancy: the runtime writes `score.json`, then `emit()` adds transport metadata `emit_ns` to the outbound object. All fields already present in `score.json` are equal; the emitted object has exactly one additional key, `emit_ns`. The frozen audit compared whole dictionaries and therefore failed.

No live case was rerun and the frozen audit is not relabelled. A separate post-hoc `audit_semantic_v2.py` compares the complete semantic score schema, requires `emit_ns` to be the only transport-only addition, verifies acquisition binding, fixture/source hashes, owner release, and independent final scorer. Result: **6/6 PASS**. This is supporting mechanism evidence, not a retroactive formal-audit pass.

## Verification

- 44/44 tests before measurement; 47/47 after the post-hoc audit correction.
- 6/6 measured first outcomes retained, no reruns.
- Independent post-hoc audit 6/6; after separate extraction, 6/6 again.
- 415 archived files enumerated.
- Raw evidence archive: 1,935,708 bytes, SHA-256 `dc3a4356ac996d9d864bd1068d3f7092fc6a0f9e126a8fdad48356487ce2a1e9` (conversation artifact, not GitHub).
- Exact source/fixture bundle is retained in GitHub as `source_bundle.tar.gz`, SHA-256 `144fc417e1d8facd699fdee7d18986665dc8d37dda482b7aa500f37617facb55`.

## H / T / D / C / U

**H:** explicit provider termination reason preserves true exit and death in the full session path while avoiding the restored-timeout wall-clock success heuristic.

**T:** six source-frozen real X11 sessions over two minimal deterministic PWAD endpoints, reusing prior timeout/running evidence rather than rerunning it.

**D:** live mechanism PASS 6/6; predeclared audit FAIL 0/6 due retained checker error; corrected independent audit PASS 6/6. Retain as integration candidate only.

**C:** tiny authored maps may not exercise natural MAP01 exit/death races; provider semantics may differ in multiplayer or other engines; input/program lifecycle, task termination, and goal success remain separate contracts.

**U:** one host, n=3 per endpoint, synthetic PWAD geometry, unpinned host frequency, observer overhead. No population interval, hard-real-time bound, or gameplay-generalization claim.

## General design implication

Do not infer task success from controller wall time. Keep **input/program lifecycle**, **provider/task termination reason**, and **goal success** separate. A program may expire after a death; a task may end by timeout without success; a successful exit may occur while the local motor program completes normally.
