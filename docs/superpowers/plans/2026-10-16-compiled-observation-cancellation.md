# Compiled semantic observation / cancellation composition

**Goal:** Check whether the compiled semantic guard added by #8982 preserves
release and prefix evidence when its read-only predicate blocks while CTRL is
held, through the actual caller and selected observation-worker option.

**Architecture:** Actual v3 helper, form, graph, adapter, bridge/store/backend/
session. Existing Fake X owner and separate reader fixtures only. Gate the
second action's semantic callback and compare synchronous and isolated routes,
with actual cancellation or an injected original-deadline crossing. Retain
before-resume thread/bitmap/receipt snapshots and real host event order.

**Constraints:** No display, native input, provider/model, WSL/container or
formal allocation. Fake cleanup timing is not physical release timing. Keep
late result rejection, unknown task effect and sticky review distinct.

- [x] Execute six conditions: stable synchronous/isolated, and cancel/expiry
  under each. Require the isolated owner to return verified fake cleanup before
  the blocked reader resumes, and retain the synchronous blocked-owner control.
- [x] Verify late callback completion cannot mutate the returned caller/core
  receipt, advance published sequence, emit suffix input or revive admission.
  Close and join all owned threads. Run affected normal/-O checks.
- [ ] Preserve source pins, raw/conditions/process streams and saved-only
  event/receipt audit; review and integrate the source-bound qualification.
