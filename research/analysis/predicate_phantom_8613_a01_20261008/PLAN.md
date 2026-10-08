# #8613 A01 — Predicate phantom membership, prospective finite study

**Status at freeze:** CONSTRUCTION ONLY; formal candidate/audit/control invocations = 0. This experiment implements a small artificial UI state machine, not the production GUI, an action-admission patch, or a user-task trial. Its purpose is to test the distinct predicate-membership hypothesis already registered in Issue #8613. Prior #4257/#4299/#8526 results and branches remain unchanged.

## Goal and precise design

A plan queries all visible, enabled `Save` controls in `dialog`. It is actionable only if the query is complete and yields exactly one target A. Between that query and an eventual *hypothetical* admission, the UI can create, remove, rename, or enable targets; replace the dialog scope; lose/recover query completeness; or change an unrelated value. No OS input is emitted. **Acceptance here is a hypothetical private proposal, never tool authority.**

Compare NODE_ONLY (revalidate original selected node's identity/aliveness/revision, ignore new matching nodes), ALWAYS_REQUERY (add final complete membership and scope identity but not intermediate history), and MEMBERSHIP_CERT (also bind complete membership/completeness change epochs). All arms are fed exactly the same trace.

For `P(v) = v.live ∧ (v.label == Save) ∧ v.enabled ∧ v.visible ∧ (v.scope == dialog)`, let `S_t={i : P(v_i(t))}`. Candidate stores initial `S_0`, selected `a` if unique/complete, original node generation `g_a(0)`, and epochs for membership `m`, completeness `c` and surface `q`. The certificate admits only if `a` remains live at the original generation, the final query is complete, `S_T=S_0`, the surface epoch is unchanged, and both `m` and `c` equal their initial values. The exact query is assumed complete when marked complete, with no hidden UI or external writer. All state changes are serially ordered by the fixture.

**Inductive contract**: each event compares the full matching set before/after and increments `m` iff it changes; any change of query-completeness increments `c`; any surface replacement increments `q`. Thus equality of all three with their starting values, plus the final set/node checks, excludes every modeled transient membership, completeness or scope change. This does *not* prove anything about an actual capture implementing these counters. An independent auditor reconstructs set membership from the raw trace without importing the candidate/model.

## Variables (SI, definitions, domains, type)

| Symbol | Meaning (Japanese) | SI unit | Definition | Domain/assumption | Type |
|---|---|---|---|---|---|
| `i` | 対象ID | 1 | A/B/C | three fixed slots | categorical scalar |
| `t, T` | 遷移の位置と終端 | 1 | discrete event count | `t=0..T`, `T=2..4` | integers |
| `v_i(t)` | UI対象の状態 | 1 | tuple(live,label,enabled,visible,scope,generation) | fully modeled fixture only | record |
| `P` | 対象述語 | 1 | above exact five-part selector | pure deterministic | Boolean map |
| `S_t` | 述語に一致する集合 | 1 | `{i:P(v_i(t))}` | subset of {A,B,C} | set |
| `a` | 当初の一意な対象 | 1 | unique `S_0` if complete | A/B/C or absent | categorical scalar |
| `g_i` | 対象版 | 1 | increases at modeled target edits | nonnegative integer; no wrap | integer |
| `m` | 述語集合世代 | 1 | increases on each result-set change | nonnegative integer; no wrap | integer |
| `c` | 完全性状態の世代 | 1 | increases on a completeness change | nonnegative integer; no wrap | integer |
| `q` | サーフェスの世代 | 1 | increases on surface replacement | nonnegative integer; no wrap | integer |
| `N` | ケース数 | 1 | `7 × (10²+10³+10⁴)` | exactly 77,700 | integer |
| `D` | 判定 | 1 | admit or refuse | Boolean, no actuation | Boolean |

**Dimension check:** set equality, revision equality and Boolean conjunctions compare only dimensionless/categorical values; `N` is a count, not seconds, rate, or cost. No SI duration, model latency, physical release or calibrated stochastic error is measured.

## H / T / D / C / U

- **H (falsifiable):** NODE_ONLY has at least one unsafe admit after a newly matching insertion; a complete MEMBERSHIP_CERT never admits a full-history-oracle-unsafe trace and never refuses an oracle-safe unchanged unique trace; ALWAYS_REQUERY can miss an insert/remove ABA.
- **T:** exhaustive product of seven initial templates and ten discrete event kinds of lengths 2/3/4: 77,700 distinct traces, one candidate Python process once. Source, executable, input generator, validation gates and audit source are source-hashed and published *before* invocation. Candidate writes one JSONL row per trace. One separate raw-only audit invocation runs after successful candidate exit; nine copied-evidence corruptions are run only after that. Construction only includes hand-selected unrelated traces and 11 unit tests, never the full corpus. No retries, replacements, exclusions or post-outcome tuning.
- **D:** PASS_PHANTOM_DETECTED_SCOPED only if 77,700/77,700 complete/ordered typed rows, planted insertion and ABA witnesses, NODE_ONLY unsafe acceptance, no MEMBERSHIP_CERT false accept or false refuse, ≥1 unaffected safe positive, raw-only audit errors empty, ≥8/9 effective corruptions rejected, unchanged source and process exit recorded. A complete candidate vs oracle contradiction is FAIL_UNSAFE_MEMBERSHIP or FAIL_OVERCONSERVATIVE; missing/incomplete source/raw/audit is HOLD/STOP. A synthetic method PASS does not establish runtime acceptance or safety.
- **C:** a fresh atomic query/scope-generation implementation or coarse invalidation might already reject these races. The certificate needs an exact membership generation and complete predicate observation; always-requery can be enough if only endpoint semantics matter. This fixture *intentionally* gives extra change history to the certificate; it does not demonstrate a latency or complexity advantage.
- **U:** partial accessibility trees, fuzzy selectors, concurrent mutation during actual query, real native backend, unknown remaps, real application/task outcomes, model calls, timings, and external author review remain outside the finite model. `u_c` and coverage factor `k` are not applicable to exact enumerated fixture outcomes; natural prevalence is unknown.

## Pre-registered command and preservation

On supplied isolated Linux x86_64 container with Python 3.13.5 and standard library, with fresh output paths and no network/GPU/GUI:

1. `cd source && python -B -m unittest discover -p 'test_*.py' -v` — construction, run before public freeze; not a formal sample.
2. After publishing source/PLAN/FREEZE hashes and verifying remote readback: `cd source && python -B run.py --out ../formal/rows.jsonl` **once**. Record actual exit, stdout, stderr, wall-clock diagnostics separately (not a benchmark), untouched input source hashes.
3. Only on candidate exit 0: `cd source && python -B audit.py ../formal/rows.jsonl --out ../formal/AUDIT.json` **once** as formal audit.
4. `cd source && python -B controls.py ../formal/rows.jsonl --out ../formal/CONTROLS.json` after audit (mutated *copies* in fresh temp paths only), do not rerun candidate.

Formal output is not overwritten; a stopped allocation stays stopped. Preserve first failures, construction logs, and all SHA-256. A same-author separate auditor is not nonauthor approval. Report exact runtime and cgroup/swap warnings; `docker`, `wslc`, OrbStack not available in this provided container, so no pinned image assertion is possible. No shared-host resource lease is inferred. No user data or input authority.

## Related domains

Database predicate/range isolation, temporal logic/model checking, GUI target identity and stale-state gating. DOI: Berenson et al. 10.1145/223784.223785; Kung & Robinson 10.1145/319566.319567. These establish general prior theory, not the validity of the synthetic GUI model in production.
