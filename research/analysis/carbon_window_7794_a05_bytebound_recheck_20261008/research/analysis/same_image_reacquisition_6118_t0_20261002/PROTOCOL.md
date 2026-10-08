# Issue #6118 T0 — same-image computation versus fresh acquisition

## H / T / D / C / U

- **H:** A finite, no-model accounting method can distinguish recomputation over immutable image bytes from acquisition at a later epoch, preserve independent-truth and trigger denominators, and prevent repeated/correlated outputs or stale images from authorizing an action.
- **T:** One deterministic seven-case table covers (a) an inferential error correctable from adequate unchanged pixels, (b) inadequate/aliased pixels where same-image rereads agree wrongly but an independent cue differs, (c) changed world after capture, (d) byte-identical recapture at a later epoch, (e) a high-confidence wrong first answer with no trigger, (f) blind reread versus answer-anchored critique, and (g) a no-error review with positive overhead. One candidate serializes visible inputs and recommendations; one separate raw-only auditor checks identities, truth, trigger, costs, and the authority firewall. The candidate never receives oracle truth.
- **D:** `PASS_METHOD_SCOPED` iff all seven predeclared rows are present exactly once; synthetic source digests and epochs reconcile; all decision-specific invariants hold; source/effect authority is never granted by review agreement; stale rows require fresh acquisition or YIELD; trigger-miss and review overhead remain in denominators; and all mutation controls are rejected. Any invariant contradiction is `FAIL_METHOD_SCOPED`; malformed or incomplete evidence is `STOP_INTEGRITY`.
- **C:** This tests the bookkeeping/decision taxonomy only. All outputs and labels are authored; fixed cost units are not wall time or model tokens. A simple YIELD or independent typed cue may dominate rereading. T0 has no vision model, PNG, GUI, action, real capture pipeline, or empirical trigger.
- **U:** No claim about visual-recognition accuracy, correction rate, calibration, token/time benefit, optimal review policy, app state, focus/target identity, persistence of hidden state, effect verification, safety, or general task performance. `PASS_METHOD_SCOPED` cannot validate T1 or any production decision.

## Frozen case matrix

| Case | Visible condition | Hidden truth (auditor only) | Required interpretation |
| --- | --- | --- | --- |
| adequate-inferential-error | adequate unchanged pixels; trigger true | first answer wrong; blind and critique corrected | correction is a same-source computation, not independent evidence |
| aliased-pixels | inadequate pixels; trigger true | blind/critique agree wrongly; independent cue differs | seek independent cue or YIELD; never vote rereads |
| changed-world | current epoch exceeds captured epoch | old answer no longer describes current world | reacquire or YIELD; old-image review cannot promote action |
| same-bytes-new-epoch | recapture digest equal, epoch advances | hidden state unresolved | report newer visual time only; no hidden-state/effect claim |
| high-confidence-trigger-miss | confidence .99; no trigger | first answer wrong | retain trigger miss; YIELD, no action |
| answer-anchoring | blind and critique disagree | blind is correct; critique is wrong | preserve both; no majority/authority |
| no-error-overhead | trigger true; review unchanged answer | first answer already correct | retain positive review cost and zero correction |

The payload strings are synthetic identity tokens, not image files. `cost_units` are arbitrary frozen ledger units, not milliseconds, dollars, or tokens. Every candidate output recommends `YIELD` or an ordinary downstream gate; no action is admitted by this T0.

## Execution boundary

Allocation: `same-image-reacquisition-6118-t0-20261002-01`. Frozen base: `abd0ce6425e24934731b763ece83421d309535b5`. Runtime: OrbStack-managed Docker, pinned `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, `linux/arm64`; network disabled; read-only root/source; only one output bind mount writable; 0.5 CPU, 256 MiB, 32 PIDs, all capabilities dropped, no-new-privileges. Candidate and auditor use separate containers. No model, provider, GUI, user data, external network, GPU, game, or OS input.

The available runtime exposes OrbStack/Docker, not an Obstac command or MCP endpoint; no claim of an Obstac-managed allocation is made. The unrelated pre-existing `unjuno-native-ci-6092` container was observed at 0.00% CPU and approximately 112 KiB memory and was left untouched. This small CPU-only run is not a reservation or transfer for other allocations.

The candidate container receives only individually mounted `candidate.py` and `fixture.json`; `truth.json` is not mounted or readable there. The formal sequence is one candidate invocation followed by one independent raw-only audit invocation if and only if the candidate exits 0. The auditor receives `audit.py`, the visible fixture, auditor-only truth, and candidate raw; the raw and all source inputs are read-only, with only its separate audit-output directory writable. No retries or post-result edits to the frozen inputs/source are allowed. Runtime receipts and hashes are retained alongside the raw table and audit.
