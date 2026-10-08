# Formal failure — Issue #8629 T0 A01

**Disposition:** `HOLD_CANDIDATE_ENTRYPOINT_NAMEERROR`  
**Allocation:** `EPISTEMIC-ACTION-8629-T0-A01-20261008`  
**Launch:** 2026-10-08T13:37:06.546641+00:00 UTC  
**Frozen source verification:** PASS  
**Retries:** 0

The single candidate invocation exited 1 before emitting any stdout. Its stderr ends in `NameError: name 'select_action' is not defined` at `candidate.py:42`; `candidate.py` calls `select_action` and `recognize_need` without importing either symbol. The single auditor invocation then received the empty candidate stdout and exited 1 with `JSONDecodeError` at byte 0. The auditor failure is a downstream consequence, not an independent audit finding.

| Receipt | Invocations | Exit | stdout bytes / SHA-256 | stderr bytes / SHA-256 |
|---|---:|---:|---|---|
| Candidate | 1 | 1 | 0 / `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 1125 / `df35649d555c2dbabba5ffe9cf2669cd594c9c6dd75efb21850c3ee57c9d3938` |
| Auditor | 1 | 1 | 0 / `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 1309 / `4c8548a9ddee7a63932b1e8a632c985bbb565a06938ea1b974b13750bbd3e12a` |

The frozen runner preserved both stderr byte streams, empty raw stdout files, exact invocation counts, environment, and receipt in `formal/`. It verified all frozen source hashes before launch. No scientific rows were produced; neither the method gate nor hypothesis gate was evaluated. This is an execution failure, not evidence for or against H.

The construction suite passed before freeze but did not exercise the candidate CLI entrypoint end-to-end. That coverage gap explains how missing imports escaped; it does not justify changing this frozen run. Do not retry or edit this allocation. Any corrected CLI/integration test and formal execution require a separately versioned successor allocation with new freeze hashes and new evidence.
