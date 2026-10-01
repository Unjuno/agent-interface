# Mixed-app formal result #2821 v17

## Scope

This is a bounded, model-free, containerized protocol result. It is not a claim about broad product reliability, human-tempo performance, or model-in-loop acceptance.

## H/T/D/C/U

### H — hypothesis

A Debian bookworm runtime with an explicitly verified Chromium executable and a full-size desktop-surface admission gate can execute the mixed-app long-session protocol without model or runtime network calls.

### T — test

Run one formal allocation with runtime networking disabled. Exercise focus drift refusal, Calc modal recovery, Calc geometry invalidation and stale refusal, Chromium window replacement and stale refusal, fresh return to Calc, and neutral cleanup.

### D — data

- GitHub Actions run: `35467904361`
- Artifact: `mixed-app-formal-allocation-2821-v3`
- Artifact ID: `10591519498`
- Decision: `PASS_MIXED_APP_LONG_SESSION_SCOPED`
- Checks: `[true,true,true,true,true]`
- Event count: `15`
- Input operations: `3`
- Container exit: `0`
- Model calls: `0`
- Network calls: `0`
- Runtime: Debian bookworm; `/usr/bin/chromium`; Chromium `153.0.8010.47`

### C — criterion

The scoped PASS requires a complete ledger, exit 0, all five checks true, zero model calls, zero runtime network calls, stale-admission refusals, fresh identity validation after transitions, and neutral cleanup. The artifact records all of these conditions.

### U — uncertainty

The result is a bounded synthetic gate. It does not establish full application reliability, model-in-loop behavior, six-task live acceptance, or human-speed performance. Earlier STOP/FAIL artifacts remain immutable and are part of the research history.

## Recorded transitions

The ledger records Inkscape `710x659`, Calc `1600x1000` then `1200x700`, Chromium replacement `10485763 -> 4194307`, focus drift refusal, modal observe-only recovery, stale geometry refusal, stale window refusal, fresh Calc return, and neutral cleanup (`cleanup_failure=false`).