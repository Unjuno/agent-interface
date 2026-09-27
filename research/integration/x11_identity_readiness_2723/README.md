# X11 mixed-app identity readiness successor (Issue #2723)

This namespace is an additive successor to #2687. It does not rewrite the Chromium-only HOLD receipt from #2687 and does not claim mixed-app acceptance.

## Frozen boundary

The experiment is read-only and model-free. It may start disposable Inkscape, LibreOffice Calc, and Chromium clients on a private X11 display, but it must not send keyboard/pointer input, call a model/provider, access task content, or infer an application effect.

## Hypothesis

Explicit process/window readiness barriers plus a WM_CLASS-capable query will produce two stable captures containing all three applications with typed, distinct identities.

## Decision contract

Emit PASS_IDENTITY_READINESS only when both captures contain all three app labels and every record has a positive integer window_id and pid, a non-empty title and WM_CLASS, stable identity fields, and distinct window/pid pairs. Otherwise emit HOLD_IDENTITY_DISCOVERY with exact missing apps/fields.

Retained data must include raw JSONL captures, timestamps, display, process identity, package/container identity, cleanup status, workflow run ID, and an independent audit. A pass here does not close #2499/#2606 and makes no claim about effects, latency, tokens, reliability, or model utility.

## H/T/D/C/U

- H: readiness barriers and a WM_CLASS-capable query resolve the prior partial observation.
- T: private X11 container; start each client; wait for its process and visible window; capture twice; audit stability and cleanup.
- D: raw captures, source/container/package manifests, stdout, audit output, and cleanup receipt.
- C: all three applications, both captures, complete typed fields, stable/distinct identities, clean shutdown.
- U: the prior run cannot yet distinguish startup timing, visibility/query semantics, or WM_CLASS exposure as the cause.

## Collision policy

All files are under this new namespace and branch. Existing #2687 receipts, identity branches, and formal acceptance work remain unchanged.
