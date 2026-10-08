# Management capture association gate

Concrete #57/#55 integration blocker discovered while following the actual
public API admission in #6323. Ordinary dispatch presentation already rejects
post-inspection errors. Public MCP management presentation instead extracted the
nested observation directly and could deliver an image despite a target/capture
association failure. A model could therefore receive inconsistent evidence from
inspection or selection, including historical lookup of that same result.

`present_management_report` now withholds the image when a needs-review report
has an error, or an explicit capture_consistency is anything other than matched.
Raw observation, error/recheck evidence and committed target selection/revision
remain present. Historical `interface_results` uses the same gate and does not
recapture, rebind or replay. Successful matched captures, input recovery and
existing guarded presentation remain covered by the prior suites. No new schema,
lease or authority is issued. This does not detect semantically stale pixels or
acknowledge redraw; the stale compact modal in #6323 remains an explicit limit.

## Validation and retained attempts

One regression covers actual public FastMCP call/results composition with a
backend test double: inspection changes during capture; committed selection
changes during capture; committed selection cannot recheck metadata. Each must
return text only, keep the original nested capture and exact retained bytes, keep
committed selection/revision where applicable, and not invoke presentation,
recapture or input. Existing positive matched-image tests still pass.

The original pre-edit test failed in all three subcases. After the product edit,
the first run exposed a test expectation mistake: transport removes the image key
from text, so asserting a null key was wrong. Corrected the assertion to absence;
no production behavior was weakened to satisfy that assertion.

`reproduce_baseline.py` is a separately retained post-edit diagnostic failure:
it copied function globals and bypassed the test's presentation patch, observed
zero regression failures, and exited 1. Do not count it as proof of baseline
correctness. The additive `reproduce_baseline_01.py` uses the exact historical
presenter AST with live module globals and reproduces all three failures, exiting
0 only for that expected negative control. Both scripts/logs remain preserved.
The original pre-edit console run is separate from this later reproduction.

- 63 targeted management/post-dispatch/guarded tests PASS normally and under -O.
- Complete native protocol and harness suites PASS; commands, timing and full
  stdout/stderr are in native/result.json and its referenced logs.
- No live GUI allocation or provider/model invocation is claimed by these tests.
  No token, latency, resource or human-tempo improvement is inferred.

This change closes the production management-delivery gap, not the frozen
admission keeper's last_native invalidation gap. A successor shared caller must
still refuse withheld/inconsistent callback evidence before formal #57 allocation.
Existing frozen studies and their outcomes are unchanged.
