# V39 post-batch per-key keymap sample A02

## H / T / D / C / U

**H:** Extending the current V12 owner's existing post-release-batch `input_state` call with one owner-thread `query_keymap` sample can bind every key's state at that shared post-batch instant, without inserting a query between explicit key-up injections.

**T:** Freeze exact current main V39 V15/backend/V4/V3/V12 sources and an experimental V12 copy. Run the production release-batch backend with its lower typed-step loop and X display replaced by inert fakes. Compare normal releases, one deliberately retained key after KeyRelease, and one injected keymap-query failure. The candidate annotates each release row only when owner, intent, keycode, and post-batch sample identity/order match.

**D:** PASS the mechanism only if normal mode has one query after both ups, reports both keycodes up at that sample, and preserves per-key owner receipt identity; retained-key mode identifies only the residual key as still down; query-error mode emits no per-key confirmation and retains incomplete/unknown telemetry. Authority and application-consumption claims must remain false in every mode.

**C:** Inert fake Xlib and a scripted typed-step base; no server, game, model, or OS input. The keymap is sampled once after the batch, so results describe each key at that shared sample time, not the exact physical transition instant.

**U:** Does not establish real X server behavior, latency, application consumption, useful feedback, threat response, recovery, or MAP01 task effect. A PASS would justify a production-equivalent follow-up, not close Issue #59.

## Reproduction

The candidate is one-shot. Run `run_candidate.py` in the frozen pinned container command recorded in `CONTAINER_EXECUTION.txt`; then run `audit.py` read-only. Results are under `results/a02/`. A01's empty-mount setup STOP is retained separately and is not scientific evidence.

## A02 result

In the normal case, both explicit-up receipts were linked to their unique admissions and to one shared keymap sample. Both keycodes were absent at that sample; the query occurred after both up RPCs returned, with zero keymap queries between the up injections. In the deliberately retained-key case, keycode 65 (`space`) remained in the fake X server keymap while keycode 38 (`a`) was absent. Existing `owner_transition_verified` remained true for both release rows because it summarizes the software owner ledger; the added sample exposed the physical-state discrepancy. Terminal cleanup then failed closed on the remaining key. In the query-error case, both release rows were emitted incomplete and no per-key result was attached.

The `PHYSICAL_STILL_DOWN_AT_POSTBATCH_SAMPLE` label in raw candidate data means only that the fake X server's `query_keymap` reported the keycode down. It does not claim real hardware state. `physical_verification_authoritative` and `application_consumption_observed` remain false. The independent audit and four mutation controls pass.
