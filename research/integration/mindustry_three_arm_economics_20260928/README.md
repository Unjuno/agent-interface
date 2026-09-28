# Mindustry three-arm economics — successor #5130

This additive package is for the unmeasured six-task Mindustry economics cell
under #57. It inherits the frozen task/order/arm/call schedule and acceptance
rule from #1679; it does not reopen or modify #1679, #2624, or prior allocations.

This branch includes current `main` `43abf7afd3df4be8afa129daed3adc72501b6a8f`
(merge commit `290ee6ef4942cc3cb3883662b98e0a9baaac54f7`).

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

No formal or live model/game allocation has run in this package. GitHub #5085
still has no named slot assignment for #5130; the latest coordinator arbitration
request favors #5133, which does not transfer a slot to this lane. Do not
treat an empty container inventory as authorization. No Docker build/pull or
experiment-image inspect was performed. A separate unallocated-container
policy violation did occur during synthetic test preparation: six short-lived
`docker run --rm` invocations were made without the required named slot. Four
failed before test cases (repository import/setup errors); two ran the six
synthetic tests successfully (6/6 each). All used the already-cached pinned
Python image, network none, read-only root and repo mounts, and bounded CPU,
memory and PIDs. The containers exited and `--rm` removed them. No Mindustry,
model, asset, GPU, formal allocation, or independent audit was invoked. This is
an execution-policy violation, not a formal result; it has been reported on
#5130 and #5085. No further Docker calls will be made on this lane until an
explicit slot assignment.

The decision-contract check is synthetic and non-scientific. It was run both
on the host and in local, network-disabled Docker containers using the
already-cached `python:3.12-slim-bookworm` image (`sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e`).
The complete repository was mounted read-only; container root was read-only,
with 1 CPU, 512 MiB memory, 32 PIDs, all capabilities dropped, and
`no-new-privileges`. The two successful invocations each passed 6/6. Four
failed before test cases: one subdirectory-mount `IndexError`, and three
repository/scorer import setup errors while correcting the mount-relative path.
All failures are retained as setup failures, not folded into the passes. The
corrected self-locating test and read-only repository mount produced:

```powershell
python -m unittest discover -s research/integration/mindustry_three_arm_economics_20260928 -p 'test_decision_contract.py' -v
```

The inherited full probe was also run on the host after syncing current main:

```powershell
python probe_integrated_efficiency_protocol_v1.py
```

Result: `passed=true`, positive disposition `RETAIN`, all 10 mutation/control
cases rejected or held as specified. This probe is synthetic too; neither it
nor the six unit tests supplies live task/economic evidence.

It checks the inherited evaluator's positive route, strict task-4 break-even
boundary (including equality failing), and fail-closed task schedule, stale
target, and repair gates. This is local containerized evaluator verification,
not construction/formal/audit under the shared allocation, and not a
model/economics result.

Refresh main and recheck issue/PR/branch/path and resource arbitration before
freezing any run.
