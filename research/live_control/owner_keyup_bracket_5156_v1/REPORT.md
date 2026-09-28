# #5156 caller-boundary analysis — scoped PASS

**Disposition:** `PASS_AUTOMATIC_RELEASE_OUTSIDE_CALLER_BRACKET` for the frozen
control-flow question. This is not a key-up timing or X11 result.

## Finding

At frozen main `16421aefa2ec357b79e3fd3dc307b32955bc6fab`, the v10 owner starts
an owner thread and `InputOwner.call()` enqueues a request, then waits for that
request's reply. The owner loop separately polls active lease state before it
dequeues the next request. Once a `down` request has returned, the owner can
observe expiry, cancellation, or focus change on a later loop turn while there
is no client call waiting. It then calls local `release(reason)` directly.

There are four local `release()` call sites in `_run`:

| Line | Trigger | Caller-boundary classification |
|---:|---|---|
| 205 | `stop_requested` | Autonomous owner-loop cleanup; on timeout the client call raises before the wrapper can record a normal return timestamp |
| 219 | expiry / cancellation / surface or focus change | Autonomous owner-loop cleanup after state polling, before dequeue |
| 261 | queued `release` or `close` operation | Client request path; can be enclosed by the v3 wrapper |
| 356 | thread finalizer | Conditional cleanup; retained separately because its caller relation depends on why the thread exited |

The v3 wrapper stamps a client `up`/`button_up` around `_inner.call()` and stamps
client `release`/`close` calls when a release receipt is returned. It has no hook
inside `_run` and cannot retroactively supply a caller return boundary around
autonomous line 219. Thus the allocation's universal nesting rule cannot apply
to both explicit client `up` and owner-triggered cancellation/expiry cleanup
without changing the contract or adding another caller-side event. No old
key-up time is inferred.

## Verification

- The frozen v10 and v3 source blobs and SHA-256 values match the declared main.
- Static analyzer: 9/9 source assertions; four release call sites classified.
- Construction controls: 6/6 pass.
- Separate AST/result auditor: PASS; 6/6 deliberately corrupted result summaries rejected.
- Result SHA-256: `4a674dd4f4929950ce689209d4cca7d80b721bf235cce5cb9424c3bb6849d6cd`.
- Audit: `AUDIT.json`, errors empty; SHA-256
  `ec92e38fff758545dcc966223fa25adfe5382b1c755ba1620ad45034af6cad8c`.

Commands are recorded in `PLAN.md`. Two analyzer iterations initially stopped on
the analyzer's own over-specific AST-unparse expectation; the implementation
was corrected before the recorded run. The independent verifier also caught a
function-selection bug and an unguarded mutation control during construction;
those were fixed before the final audit. These construction defects are retained
in local command history, not misrepresented as source findings.

## Limits and disposition of the formal allocation

No owner was imported or executed. No X11/XTest, XSync timing, container, GUI,
model/provider, GPU, or input was used. This result neither verifies that the
current telemetry interval is narrower nor establishes physical key-up or
application consumption.

Do not launch the registered X11 formal under its current universal nesting
gate. Preserve it unspent. A valid successor must scope caller nesting to
client-requested explicit `up`, and classify autonomous cancellation/expiry
cleanup separately (or freeze a new explicit causal caller event). Only after
that decision, construction controls, and a fresh exact-lane shared-container
lease may the disposable X11 allocation run.
