# A03 preregistration — V39 per-key release closure on Xvfb

## H / T / D / C / U

**H.** The current-main V39 `doom_owner_thread_release_batch_backend_v1.Backend.raw()` composed with release telemetry v2, transition owner v4→v3, and input owner v12 will issue 40 admissions and 40 identity-joined key-up receipts across 30 release batches. All 80 XTest edges will reach only the focused Xvfb client in the fixed sequence. Every explicit owner-thread KeyRelease/XSync will complete before the next key edge in its release order; no owner keymap query will occur between explicit key-ups. After each completed batch, an independent observer connection will query the X server keymap and find both test keys up. Owner shutdown must verify empty state and terminate.

**T.** On the attached WSL environment, launch one local, TCP-disabled Xvfb instance on display `:125`, create and focus one client window, and invoke the exact copied current-main release-batch backend through a minimal executor parent shim. Each batch executes one `a` press/release, a repeated `a` press/release, or the chord `a down`, `space down`, `space up`, `a up`. Read client events only after each batch has completed; query keymap only after the full batch. Instrument `Display.query_keymap` to distinguish observer queries from owner queries. Capture all raw admissions, release receipts, client events, owner explicit key-up timestamps, post-batch keymaps, terminal owner cleanup, and Xvfb exit.

**D.** `PASS_METHOD_SCOPED` requires frozen source/candidate hashes, 40 distinct `(identifier, step, key)` admissions, 40 matching receipts, 80 correctly ordered client events, 30 empty post-batch keymaps, complete owner release-batch receipts, no owner keymap query before the last explicit key-up, an empty verified owner close, a stopped owner thread, and Xvfb exit 0. A complete mismatch is `FAIL`; setup/import/trace/cleanup failure is `STOP`. Candidate runs once; raw-only auditor runs once only if raw evidence exists. No reruns or overwrites.

**C.** Exercises current-main release-batch backend and owner transition composition against a local synthetic X server and one X client. The immediate parent backend is a minimal fixture shim. The Xvfb arguments disable TCP and do not connect to a game, desktop window, physical device, or network service.

**U.** This qualifies a software instrumentation path and receipt ordering only. Xvfb event dispatch and keymap state do not prove physical keyboard state or application consumption. The experiment says nothing about live gameplay, threat response, model interruption, useful feedback, recovery, terminal task result, or latency under actual game load. It does not allocate Issue #59's private game lane.

## Immutable outcome policy

The current main SHA is `d3a51bc4c962b223d05280225042b96a033df8bf`. All copied production source hashes, static V15 startup selectors, candidate, and auditor are in `FREEZE.json`. The one-shot raw result is `results/A03/RAW.json`; do not invoke the candidate again if any outcome file exists. The auditor must preserve `PASS_METHOD_SCOPED`, `FAIL`, or `STOP` as observed and may not reinterpret a setup failure as a completed test.
