# Owned public MCP: lifecycle and explicit modal review

## Outcome

Experimental, explicit `--session-mode persistent-x11` now holds one X11 session for the existing public observe/dispatch facades. Default one-shot behavior remains. Busy calls refuse; no automatic reconnect/replay occurs. Retained results and explicit close preserve cleanup evidence. Target review separates inspecting the focused client from explicitly selecting it, with a fresh metadata recheck and monotonically increasing session binding revision.

The primary agent used the public MCP tools over the official Python MCP client. First Calc trial failed at the original window's focus while its format dialog was active; no save occurred. A diagnostic established that the modal was a separate managed window. After integration of explicit target review, a new task saved 597/624 and independently verified the XLSX, returned the target to the main window, and closed with verified input release. Input went through ordinary public dispatch, without research visual-guard overrides or a helper model.

## Retained attempts

- `public-owned-mcp-implementation-01`: original implementation/build checks, including missing-optional-dependency regression and correction.
- `public-owned-mcp-live-01`: SDK dependency-path failure before fixture creation; raw terminal traceback was not separately saved, so only the recorded failure summary is bundled.
- `public-owned-mcp-live-02`: private real X11/stdio read-only session reuse, explicit close, refusal after close and retained result reads (source 62c63931a).
- `public-owned-calc-primary-01`: source 2fce524d5, seed 991302; values 666/820 visible but independent saved file [null,null]. Three dispatch requests: first completed, main-window focus failed, no-focus pointer attempt refused. Explicit observations were used between attempts; all records retained.
- `public-owned-focus-diagnostic-01`: fixed diagnostic script emitted input, then failed serializing X11 bytes metadata; terminal exit 1. Failure summary retained, no invented missing result rows.
- `public-owned-focus-diagnostic-02`: corrected serializer, same seed 991303; actual focus ancestry and window list prove the separate modal, and original focus verification failed. Exit 0. Diagnostic only, not a primary-operated task or save.
- `public-owned-calc-primary-02`: source eb539b185, seed 991304; primary-operated save succeeded, [597,624]. Two completed input dispatches; two explicit target reviews (to modal and back), three standalone captures including initial, two inspections and close. All ten calls use one session. Client/fixture runner exit 0; fixture close returned.
- `public-owned-target-check-01`: source 685b9f3fe common check, 192 protocol + 79 harness tests passed.
- `public-owned-final-check-01`: 27 public MCP tests and 7 portable distribution tests passed.

Primary reviews describe which screenshots were actually viewed and what they support. `timings.json` reports exact SDK call boundaries only. Source freeze files retain full original SHAs; later rebasing/documentation does not rewrite those live identities.

## Limits and decision

This supports an opt-in X11 integration path and one successful new Calc save, not generic modal recovery, a cross-app acceptance threshold, visual freshness authority, lower latency or reduced tokens. The initial failure and final success use different values and are not a controlled comparison. Explicit review adds roundtrips. WM title/class/transient metadata is not authenticated identity, native IDs can be reused, and no atomicity between inspection, screenshot and later input is claimed. Input recovery is never cleared by target review. Observation and lease assertions remain caller supplied; default one-shot does not acquire a new binding contract.

No automatic modal selection/dismissal, sensor logic or helper-model route is introduced. Broader research acceptance criteria, including #2195, remain unproven. Abrupt process kill cannot guarantee cleanup. A successful fixture close is not independent proof that every descendant exited. Product-host MCP reload is also separate from this direct stdio SDK validation.

Run `python runtime/results/public-owned-mcp-01/verify.py` with openpyxl. The verifier checks archived bytes, recorded lifecycle and independently rereads both saved XLSX files. It does not infer performance, visual understanding or general reliability from hashes.