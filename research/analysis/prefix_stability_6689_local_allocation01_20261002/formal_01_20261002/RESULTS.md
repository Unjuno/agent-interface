# Issue #6689 T0 result — 2026-10-02

## Final preregistered disposition: `FAIL_METHOD` (posthoc qualification)

The unchanged audit JSON emitted `PASS_METHOD_SCOPED`, but that receipt does not satisfy the preregistered D rule. The candidate and auditor both treat `mandatory_fail=true` as if the mandatory-check vector were complete, even though the finite state has no vector-completion event and `mandatory_all_pass=false`. Both omit the still-pending `mandatory_check_vector` obligation on such negative states. Read-only posthoc counting over the retained, independently accepted raw found **192** `STABLE_FINAL_FAIL` states with this omission. The representative prefix `mandatory_fail → generation_sealed` has both sources still open and the mandatory vector incomplete, yet its pending list reports only the two source completions. This is a failure of the method/contract and a missed corruption/acceptance condition, so final disposition is `FAIL_METHOD`, not PASS.

Preserve the original auditor receipt below verbatim as an observed output; it is not the final acceptance decision. Candidate/auditor/retries remain 1/1/0. No code, raw, audit JSON, or frozen input was modified, and neither formal executable was rerun. See [ADJUDICATION.md](ADJUDICATION.md).

## Original independent audit output (preserved)

`PASS_METHOD_SCOPED`. One WSLc candidate and one separate raw-only auditor completed, exit 0; retries 0. The candidate emitted 769 records: 768 reachable finite prefix states plus one explicitly unknown-contract case. Candidate raw SHA-256: `f95ef664ebfc663a784747297e493dc3c5cd0e4b1adc8d26e9c2bb7e887644e3`. Independent audit JSON SHA-256: `e093260fe645a5ebb2476a18f3b366f1f98200cf3e4586d3a992fd6c6e999b2a`.

The auditor independently reconstructed the 768-state transition graph, each representative event prefix, each state’s set of all legal terminal outcomes, and its classification. Errors: `[]`. All four frozen controls were rejected: mandatory-failure omission, forged source closure, stale-generation relabeling, and timeout treated as completion.

## Enumerated outcomes

| Classification | Prefix states |
|---|---:|
| `STABLE_FINAL_FAIL` | 480 |
| `STABLE_FINAL_PASS` | 12 |
| `CLOSED_FRONTIER_REQUIRED` | 48 |
| `PROVISIONAL` | 228 |
| `UNKNOWN` (unspecified contract) | 1 |

The candidate-reported raw labels 396 stable-negative states with at least one pending obligation; shortest representative prefix length is two events. However, the omission identified above means this cannot be treated as a valid wait-for-all comparison: the finite model has no explicit mandatory-vector completion event for the negative branch, so the baseline count is not identifiable from this encoding. This is structural method evidence, not a timed latency estimate; the fixture has no arrival-time distribution and no wall-clock benefit was measured. The deadline-only baseline cannot finalize before its declared cutoff by construction.

## Runtime and limits

Windows host via WSLc 3.0.1.0, cached image `python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016` (linux/amd64), Python 3.12.15, pull never, network none, one CPU and 512 MiB requested. The kernel warned cgroup/swap limits are unsupported; effective memory enforcement is unverified and no memory-limit claim is made. No GPU, GUI, model, provider, task input, user data, or external effect.

The state machine and its finite continuation language are authored. This result does not establish live verifier correctness, a real-system latency reduction, truth/freshness, action safety, or general asynchronous-system behavior. Stability is not actuation authority.
