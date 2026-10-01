# Issue #5702 T0 preregistration — 2026-10-01

## H / T / D / C / U

**H.** In a finite fixed opportunity stream, reducing interface action cost can leave a frozen-start workload unchanged, enable beneficial expansion, or change optional task mix so that a plausible ex-ante-positive task displaces a higher-value task under fixed resource/verifier budgets. Reporting fixed-workload and all-opportunity/session outcomes separately detects these distinct cases. This is a constructed method hypothesis only; no real agent rebound is predicted.

**T.** Exact deterministic no-model decision table based on Issue #5702 and freeze clarification comment #5923389962. Every opportunity is declared before route assignment. Two route arms (`slow`, `fast`) receive identical opportunity IDs, arrival order, values, effects, and budgets. Run three cases:

1. `no_rebound`: frozen-start policy starts the same mandatory verified task and the same mandatory UNKNOWN endpoint task under both routes; optional rows and a high-value unsafe row remain in the denominator. Only per-action/resource cost changes.
2. `beneficial_expansion`: the same threshold policy and two safe opportunities; faster costs make an ex-ante-positive optional task fit the fixed budget, and the frozen independent endpoint is useful.
3. `adverse_mix`: the same threshold policy, task sequence, and budget. Under `slow`, the positive-value low task fails the ex-ante net-value threshold and a higher-value task fits. Under `fast`, the low task becomes ex-ante positive, is started, consumes fixed verifier/resource capacity, and crowds out the higher-value task. Its independently fixed endpoint value is lower than its ex-ante estimate; no label is changed after observing a route.

All arms retain every offered row, including skipped and unsafe opportunities. Hard safety is non-compensable: the high-value forbidden row must never start. Costs, verifier demand, endpoint UNKNOWN, starts, completions, and net useful value are separate fields. A fourth control corrupts the opportunity denominator and must fail closed. The candidate emits one canonical JSON object; a separate auditor independently reconstructs it from the frozen table and does not import candidate code.

**D.** `PASS_METHOD_SCOPED` only if: matched opportunity IDs/order are identical; frozen-start counts/endpoint labels match; `slow`/`fast` common-task costs show the preregistered reduction; beneficial expansion increases verified net useful value; adverse mix lowers verified net useful value despite lower common-task cost and retains skipped high-value/unsafe rows; UNKNOWN is not scored as success; unsafe task starts remain zero; the independent raw-only audit passes and all eight corruption controls are rejected. Otherwise `FAIL_METHOD` or `HOLD` per the observed gate. No empirical rebound claim follows.

**C.** The table is hand-authored and its policy/value bands are deterministic. The opportunity mix, route cost, verifier demand and outcomes are coupled by construction. A method pass validates denominator and accounting behavior, not a real agent's adaptive behavior or any task's subjective value.

**U.** Unknown task value, model choice, queue interference, longer-horizon effects, and task heterogeneity remain untested. Net useful-value arithmetic is a synthetic scoring device, not safety utility; any forbidden effect independently fails regardless of aggregate value.

## Freeze identities

- Issue: `Unjuno/agent-interface#5702`; preregistration clarification: comment `#5923389962`.
- Source main: `4bf4cb04eade179be9f5a25b130ebe53ea3a71b7`.
- Branch: `research/endogenous-demand-rebound-5702-t0-20261001`.
- Evidence path: `research/analysis/endogenous_demand_rebound_5702_t0_v1/`.
- This T0 is explicitly no-model and requests no container/GPU allocation. Obstac is unavailable in this tool/runtime inventory; because the issue's T0 is a tiny deterministic stdlib decision table with no resource request, execute on CPython 3.12. Do not interpret host execution as container validation.
- One formal candidate CLI invocation after source/test review and the GitHub freeze record; only on its successful JSON output, one independent raw-only audit. No retries.

At freeze-commit time, record exact source/test SHA-256 values and GitHub commit. Raw formal output is created only after the freeze is published.
