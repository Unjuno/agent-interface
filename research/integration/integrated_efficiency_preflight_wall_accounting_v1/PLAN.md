# Integrated efficiency preflight wall accounting v1

Task: `INTEGRATED-EFFICIENCY-PREFLIGHT-WALL-ACCOUNTING-20260917-001`  
Issue: #829  
Immutable base: `40072ec1962afe9fe1a9f6ade79ce36a2e8cc93f`

This is a container-only posthoc accounting repair for #57. It does not rerun the retained live three-arm comparison and does not invoke a model, GUI, provider, or task input.

## H

The retained `audit.elapsed_ms` values are task-phase sums because the scoring protocol sums only six task `elapsed_ns` values. Exact retained schema-preflight records contain nonzero wall intervals. Adding those sequential preflight intervals should produce phase-complete totals while preserving the descriptive ordering `persistent < plain` and `persistent < ephemeral`.

## T

`fixture.json` embeds the exact UTF-8 bytes of the retained audit, three preflight result JSON records and three model-subprocess process records. The runner re-derives each source's Git blob SHA before parsing it. It computes phase-complete elapsed as task-phase elapsed + preflight elapsed. Subprocess lifetime is a diagnostic only and is not labelled model inference time.

Formal runner is executed exactly once after remote source freeze and requires `RESULT.json` to be absent. The independent auditor recomputes every derived value without importing the runner.

## D

PASS only under the exact decision rule recorded in Issue #829. Any source mismatch is integrity failure; missing retained preflight wall evidence is HOLD; reversed descriptive ordering is FAIL.

## C / U

The correction is posthoc and scoped to the retained sequential schedule. It does not establish causal speedup, population latency, provider inference time, monetary cost, human tempo, or second-domain performance. Preflight input tokens were already charged in the retained token comparison; token break-even is intentionally not recomputed here.
