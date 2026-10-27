# Result — Issue #8613 A01: predicate membership phantoms

**Disposition:** `PASS_PHANTOM_DETECTED_SCOPED` for an enumerated *synthetic method contract*, **not** current-runtime, GUI, task-effect, input-authority or product PASS.

## Question and actual result

A query initially finds exactly one `Save` target in a dialog. Another matching target can appear before hypothetical admission while the old target's own node generation remains unchanged. Does node-only validation miss the changed match set; can a history-bound predicate certificate reject it without rejecting unchanged unique cases?

**Exactly 77,700 exhaustive finite histories** were evaluated: seven initial UI configurations, ten possible transition symbols, lengths two/three/four, each sequence once. One candidate process; one separately executed independently coded raw-only audit; nine copied-record controls after. Every row was retained including initial-empty, initially-ambiguous and incomplete negative cases. No live GUI, X11, model call, external action, GPU or shared desktop.

| Decision endpoint | Count across 77,700 | Meaning |
|---|---:|---|
| Full-history-oracle safe and unique | 1,277 | Eligible only inside authored model |
| NODE_ONLY positive admissions | 14,742 | 13,465 oracle-unsafe admissions |
| ALWAYS_REQUERY positive admissions | 2,543 | 1,266 oracle-unsafe admissions; endpoint check misses history |
| MEMBERSHIP_CERT positive admissions | 1,277 | 0 oracle-unsafe, 0 oracle-safe false refusals |
| Explicit inserted-target phantom witness cases | 819 | Subset of old-node false admissions, not independent subjects |
| Explicit insert/remove ABA endpoint-witness cases | 35 | Subset with requery mistaken acceptance |
| Evidence corruption controls | 9/9 rejected | After intact original audit passed |

**Concrete counterexamples:** `unique + [insert_B, unrelated]`: A's node generation unchanged; newly inserted B is also an eligible `Save`; NODE_ONLY admits despite ambiguous target set. `unique + [insert_B, remove_B]`: the match set returns to original, so endpoint-only requery admits, but a membership epoch detects the intervening insert/remove. `unique + [unrelated, unrelated]`: all policies admit and the oracle accepts. These cases are deterministic examples, not estimated population rates.

## First-outcome provenance

- Intake main `f99ac0d3ad084c244cc7558d2219ac87247ded0c`; user-specified project direction `docs/CURRENT_GOAL.md` experiment-first.
- Issue #8613 A01 claim before execution and exclusive additive branch `research/8613-phantom-a01-20261008`; no #8613 comments, same-topic PR or phantom branch found at scoped intake, unpushed work unknown.
- **Prospective public freeze:** commit `df729d5e9ea23761156406c34f0f9e5d09c94ba4`, full `FROZEN_SOURCE.tar.xz` Git blob `2c51783143858f64af0b2d7e8a5a25e3d64509bf`, SHA256 `9df12e0fbdc32d278c3bafcec6154798602b08b2ae6fdeff69a04fbf310dad32`; readback confirmed before the only formal candidate invocation. 8 source/PLAN/environment hashes in frozen SHA256SUMS.
- Excluded TDD/setup: first RED import STOP (model.py not yet created), later 11/11 construction unit tests PASS. Neither is a frozen-case sample.
- Formal command: `cd source && python -B run.py --out ../formal/rows.jsonl`, exit0, pid1724, stdout `CANDIDATE.stdout`, stderr empty, 77,700 full rows. Raw SHA256 `e6c4e05f105a8009abe3242da19f9d845bedbdc660cb334f30d4808441d218a7`.
- Separate unchanged raw-only auditor: `python -B audit.py ../formal/rows.jsonl --out ../formal/AUDIT.json`, exit0, errors=[], recorded audit SHA256 `9ae7072eb5d6ec007631ce01d76c249faaf6772634b03bb84725f0c9abc53ea5`.
- Controls: `python -B controls.py ../formal/rows.jsonl --out ../formal/CONTROLS.json`, exit0, all nine effective copied-evidence mutations rejected. They changed copied rows, never the original.
- Candidate invocations =1; auditor invocations =1; formal reruns/replacements/exclusions/post-freeze source changes = 0. Separate audit/control run from saved rows does not consume another candidate allocation.

## Correctness argument and important limitation

The `MEMBERSHIP_CERT` mechanism stores per-predicate membership change epoch, completeness transition epoch and scope-generation epoch, alongside original selected node generation and exact result set. The transition function increments membership epoch on every actual set membership change, including changes later reverted. Equality of the monotonic counters to the initial values therefore implies no such change in the serial finite trace. An independent auditor parses and replays the raw sequence itself to construct a full-history oracle; it imports neither candidate nor model. All 77,700 candidate decisions matched. This is a *conditional invariant proof/test*, not evidence that a real GUI observer can provide complete, unforgeable or atomic predicate generations.

An always-requery implementation might have lower engineering complexity if only final-state identity matters and changes during the window do not invalidate semantics. Other systems can already invalidate coarse scope generations, but might falsely refuse irrelevant modifications. This study deliberately includes both source-query completeness and historical coherence as acceptance conditions; redefining them changes the task, not the observed counts.

## H / T / D / C / U

- **H:** NODE_ONLY can admit a phantom; a full predicate-membership certificate excludes all unsafe histories and retains all safe unique histories; requery endpoint can miss ABA. **Supported within model only.**
- **T:** exhaustive finite corpus (7 initial templates × (10² + 10³ + 10⁴) = 77,700 traces), one candidate/one independent audit, nine copied-evidence control runs, 11 separate construction methods; source/gate public freeze before formal.
- **D:** `PASS_PHANTOM_DETECTED_SCOPED`: complete rows, planted phantom and ABA, 0 certificate false accept/false refusal, 9/9 corruption rejection, processes exited0. Runtime promotion **HOLD** pending real observation completeness and nonauthor review.
- **C:** Existing atomic snapshot or scope-wide invalidation may avoid the same gap; membership epochs require exact event provenance and may be expensive; endpoint semantics could be sufficient for some tasks.
- **U:** No real UI/backend, X11/Wayland/Windows/macOS, hidden nodes, screenshot or accessibility completeness, concurrent writer racing admission, semantic grounding, model/useful feedback, token, latency, survival, cost, human tempo, effect oracle or task success. Natural error frequency unknown. Exact finite integer values have no stochastic `u_c`/coverage `k` estimate. Same-author independent code is not independent human review.

## Environment and resource constraints

Provided private Linux x86_64 container; CPython3.13.5, kernel6.18.44, affinity CPU 0-4, cgroup `0::/`, `memory.max=4294967296`, `memory.swap.max=max` (not proof of effective enforcement). Docker/WSLc/OrbStack commands unavailable; no pinned container image SHA or cross-runtime equivalence asserted. No network experiment, package installation, model provider, shared GPU/GUI, OS task input or other-worker branch changes. Diagnostic candidate computation time 961,400,041 monotonic nanoseconds is **not** a frequency-controlled performance benchmark.

## Review and reproduction

Study path `research/analysis/predicate_phantom_8613_a01_20261008/**` only. Complete frozen source archive and complete raw result capsule are published as Git objects with byte/hash manifests. From a trusted extracted study directory with standard-library CPython3.13, run the saved-evidence verifier (not `run.py`). It validates source and raw checksums, recomputes the independent raw-only oracle and corruption controls from saved rows, and does not repeat the science.

No reviewer/source author other than this assistant approved the findings. Integration requires checks at actual PR HEAD, genuine nonauthor code/evidence review and a separate independent GUI/observation qualification. Do not merge merely because the finite method passes. #4257/#4299/#8526/#57/#59/global ROADMAP remain open; former experiments and STOPs unchanged.
