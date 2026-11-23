# Chromium / caller-v3 smoke R06

**Disposition: `PASS_SCOPED_EDGE_CALLER_V3_SMOKE`.** This closes only the
one-case local Edge adapter smoke described below. It does not close Issue #57
or establish matched efficiency, recovery reliability, MAP01, or Research
Preview readiness.

## Run and independent checks

- Base main: `759d15697be34a5db1afd6215b46ecf4e42d40d1`; frozen run source:
  `9cfe8433f35acbe146131f9d82f3eecb0722f44a`.
- Windows 10, CPython 3.11.9, headless Edge `Edg/157.0.4341.60`.
- One private loopback form, task token `t991025-4`, and one Submit action.
  The field was prepopulated; no entry keystroke was tested.
- The model path was an offline contract fixture: one accounted caller attempt,
  one visible-image accounting field, zero input/output tokens, zero wait.
  This is not provider usage or efficiency evidence.
- Pre-action OCR read `t991025-4`; final observation recorded changed submission
  pixels. The local server independently received exactly one
  `value=t991025-4` POST.
- The compiled receipt recorded one completed transition with verified release;
  the outer caller recorded `TASK_SUCCEEDED` from its separate HTTP effect
  scorer.
- Edge returned 0, its private profile/temp root was removed, and both retained
  PNG hashes matched the saved observations.
- The raw-data-only auditor returned `PASS_SCOPED_EDGE_CALLER_V3_SMOKE` both
  normally and under `-O`. Caller v3, compiled handoff v2 and persistent
  grounding adapter tests passed 32/32 in each mode. The profile cleanup test
  passed 1/1 in each mode. The one Edge task was run once, normally.

Raw conditions, captures, caller/model ledgers, the compiled receipt, exact
POST, cleanup record and both audit outputs are in [`raw/`](raw/). The
manifest records their SHA-256 hashes.

## Limits and next gate

The run is one controlled task, not a treatment comparison. The provider is a
fixture, the token is prepopulated, and no target-generation mutation or
two-action entry was exercised. V5's real target-handle generation/mint and
guarded admission workflow is still not bridged into this v3 path. There is no
cold/warm/invalidation/repair schedule, matched arm, live-provider accounting,
or lifecycle denominator here. Do not infer a speedup from the zero-token
fixture or the 2.9-second test duration.

Next #57 gate: adapt the established V5 Chromium target-handle/generation and
retained-evidence path to the v3 caller, then verify it on that exact source
before freezing any matched plain/current/compiled allocation. R01-R05 stops
and their audit failures remain preserved in adjacent packets.
