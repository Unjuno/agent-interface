# Mindustry three-arm economics — successor #5130

This additive package is for the unmeasured six-task Mindustry economics cell
under #57. It inherits the frozen task/order/arm/call schedule and acceptance
rule from #1679; it does not reopen or modify #1679, #2624, or prior allocations.

## H / T / D / C / U

- **H:** The persistent route `cold,reuse,reuse,repair,reuse,reuse` completes
  all six exact tasks without stale-target admissions and beats both controls
  in input tokens and planner generations, with strict token break-even by
  task 4.
- **T:** `plain`, `ephemeral`, and `persistent`; task layouts A/A/A/B/B/B;
  fresh no-image schema preflight counted once per arm; score before reset;
  one A→B geometry mutation after A3 reset witness and before B1; one formal
  allocation and a separate raw-only audit, after a named local CPU Docker
  slot and a fresh source/image/asset freeze.
- **D:** `RETAIN` only if all task effects/release checks pass, persistent
  old-target admissions are zero, repair succeeds, persistent final input
  tokens and generations are each strictly below both controls, and strict
  input-token break-even occurs by task 4. Wall time is descriptive. Missing
  provenance/resources/audit is STOP/HOLD; no population/product claim.
- **C:** Matched task sequence, model, preflight, image, task scoring and
  accounting are fixed; one intended layout change is the invalidation.
- **U:** One six-task allocation only; no general reliability, human-tempo,
  cross-domain, or product-readiness inference.

## Current status

No formal or live model/game allocation has run in this package. Docker has not
been invoked for it. Shared CPU slot #5073 was released, but a named successor
slot for #5130 is still pending arbitration. Do not treat an empty container
inventory as authorization.

The source-only decision-contract check is synthetic and non-scientific:

```powershell
python -m unittest discover -s research/integration/mindustry_three_arm_economics_20260928 -p 'test_decision_contract.py' -v
```

It checks the inherited evaluator's positive route, strict task-4 break-even
boundary (including equality failing), and fail-closed task schedule, stale
target, and repair gates. Six tests pass. This is not a model/economics result.

At this preparation checkpoint the clean local branch was fast-forwarded to
current `main` `e8b4071931df81b3408a5d0a91c7607c6323c9c9`. Refresh main and
recheck issue/PR/branch/path and resource arbitration before freezing any run.
