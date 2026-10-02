# Issue #5927 — epistemic-necessity controls T0

**Disposition: `PASS_METHOD_SCOPED`.** A source-pinned finite experiment in OrbStack distinguished action intent/dispatch acknowledgement from verified effect, while correctly requiring no *additional* exchange when a fresh local typed effect receipt was already in the current transcript.

## Executed result

- `known-save-intent-effect-unknown`: the two authored worlds share the planner's intended save action and a dispatch acknowledgement, but their safe progress actions are disjoint. Minimum additional exchange: **1**, `independent_persistence_receipt`.
- `fresh-local-receipt-no-extra-tool`: a fresh local typed `saved=true/false` receipt already partitions those worlds in the current transcript. Minimum additional exchanges: **0**; no extra screenshot/model/tool call is needed for the declared completion-versus-recovery decision.
- Construction/mutation suite: 7/7 passed in the pinned container. Candidate ran once (exit 0); a separate raw-only auditor ran once (exit 0, `PASS_RAW_AUDIT`, errors `[]`). Retries: 0.
- Raw candidate SHA-256: `868dfc7aa21de534575d599f928978da4f133b903ca26f6355a377c02b3875c8`; raw audit SHA-256: `05e469f1eb8b362de6504f70a45ca7223443a9cc741efa3c8c6335ba90f664d9`.

## Method and controls

The package enumerates current-transcript channels separately from future exchanges, so information already available is not counted as a new interaction. Controls reject a false zero-exchange candidate, an undeclared channel, a mismatched safe-action oracle, and reliance on a stale current receipt. Before formal execution, a host-side module-qualified unittest invocation failed with `ModuleNotFoundError: auditor`; it was preserved verbatim, candidate/auditor counts remained zero, and the corrected discovery invocation passed 7/7. This setup error did not consume or retry either formal invocation.

## H / T / D / C / U

- **H:** Knowing the intended save action and receiving dispatch acknowledgement does not prove persistence; one new independent persistence receipt is necessary in the positive pair. When a fresh local typed effect receipt is already current and available, no additional exchange is required.
- **T:** Two finite authored worlds and two current-transcript/control conditions. Candidate and independently authored auditor ran in separate pinned `linux/arm64` Python 3.12.14 containers, network disabled, read-only root and input, with 1 CPU / 128 MiB / 32 PID limits requested. The existing worker container was left untouched.
- **D:** Both audited minima matched the preregistration (1 and 0), all seven construction/mutation tests passed, and the separate auditor reported zero errors; therefore `PASS_METHOD_SCOPED`.
- **C:** The world pair, receipt source/truth/freshness and safe-action oracle are fixtures. “Independent” means a separate declared evidence channel in this fixture, not empirically verified independence of a live backend.
- **U:** This is a finite method/control result only. It does not establish universal feedback or model-call lower bounds, real application persistence, live GUI necessity, task completion, safety, latency, token/cost savings, or product benefit. Container limits were requested but not independently measured.

## Reproduction and provenance

Allocation/freeze and every source/input/output digest are in `FREEZE.json`, `RUN.json`, and `SHA256SUMS`. Exact raw outputs and stdout are retained under `results/`. The host construction invocation error and correction are preserved in `PRE_FORMAL.json` and the adjacent logs. Prior #5927 allocations and PR #6393 are unchanged.
