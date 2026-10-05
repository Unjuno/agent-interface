# V39 post-batch per-key keymap sample A01

## H / T / D / C / U

**H:** Extending the current V12 owner's existing post-release-batch `input_state` call with one owner-thread `query_keymap` sample can bind every key's state at that shared post-batch instant, without inserting a query between explicit key-up injections.

**T:** Freeze exact current main V39 V15/backend/V4/V3/V12 sources and an experimental V12 copy. Run the production release-batch backend with its lower typed-step loop and X display replaced by inert fakes. Compare normal releases, one deliberately retained key after KeyRelease, and one injected keymap-query failure. The candidate annotates each release row only when owner, intent, keycode, and post-batch sample identity/order match.

**D:** PASS the mechanism only if normal mode has one query after both ups, reports both keycodes up at that sample, and preserves per-key owner receipt identity; retained-key mode identifies only the residual key as still down; query-error mode emits no per-key confirmation and retains incomplete/unknown telemetry. Authority and application-consumption claims must remain false in every mode.

**C:** Inert fake Xlib and a scripted typed-step base; no server, game, model, or OS input. The keymap is sampled once after the batch, so results describe each key at that shared sample time, not the exact physical transition instant.

**U:** Does not establish real X server behavior, latency, application consumption, useful feedback, threat response, recovery, or MAP01 task effect. A PASS would justify a production-equivalent follow-up, not close Issue #59.

## Reproduction

The candidate is one-shot. Run `run_candidate.py` in the frozen pinned container command recorded in `CONTAINER_EXECUTION.txt`; then run `audit.py` read-only. Results are under `results/a01/`.
