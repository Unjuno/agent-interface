# Chromium V5 handles through adaptive caller v3 R01

**Disposition: `PASS_SCOPED_FAKE_V5_TO_CALLER_V3_COMPOSITION`.** The exact V5
point-mint method, real session-scoped `TargetHandleStore`, adaptive caller v3,
and compiled GUI runtime ran as one local composition with positive and
changed-generation cases. The frozen 25-test bundle passed 25/25 normally and
25/25 under `-O` on Windows CPython 3.11.9.

## Positive path

- The V5 method minted separate textured `field` and `submit` aliases from
  retained model-point source pixels. Each alias maps to a private random
  registry ID that was not exposed.
- Caller v3 reused and revalidated those aliases, then its final selected
  target constructed the compiled two-step form interface.
- Both aliases resolved against fresh observations and the real
  `TargetHandleStore` before action dispatch.
- Fake `enter_exact_token` and `activate_submit` terminals each reported
  verified neutral release. Both compiled effect checks passed, and the
  independent outer scorer returned `TASK_SUCCEEDED`.

## Changed-generation negative

After the entry action returned a verified release, the fake target window
generation changed while its pixels, focus, surface, geometry, and high-level
form predicates remained the same. The next `submit` observation reached the
actual store, which returned `SCOPE_MISMATCH` with
`window_generation_changed_or_missing`. The compiled runtime refused Submit
before its execute adapter. Caller v3 retained one completed/released action
and returned `EXECUTION_INCOMPLETE` / `confirmed_partial`; the independent
outer task scorer was not called.

Conditions, exact source hashes, normal and optimized output, and exit codes are
retained in [`raw/`](raw/) and the packet manifest. The executable assertions
are in `research/live_control/test_chromium_v5_caller_v3_composition_v1.py`.

## Limits and next gate

This composes the local V5 mint/store with caller v3 and compiled execution,
but all captures and I/O are synthetic; no browser, X server, OS input,
external model/provider, task application, or live allocation ran. The warm
reuse path made zero model calls, so there is no token, latency, cost, or
efficiency result. It does not establish repeated recovery reliability or
Research Preview readiness.

The next #57 step is a prospectively permitted live execution using the exact
same generation/capture/admission/release/effect joins and all-attempt provider
accounting, before freezing a matched cold/warm/invalidation/repair comparison.
Keep #57 open.
