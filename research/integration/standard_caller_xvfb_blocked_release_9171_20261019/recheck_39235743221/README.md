# Standard MCP Xvfb blocked-release recheck — run 39235743221

Additive record for GitHub Actions run [39235743221](https://github.com/Unjuno/agent-interface/actions/runs/39235743221), PR [#9171](https://github.com/Unjuno/agent-interface/pull/9171), after the 1.5 s retired-release worker window change. The prior first and second outcomes remain unchanged.

## Frozen identity and scope

- PR head SHA: `3b94963440a2fc1bef4b3da89d40626e3c4044f3`; base SHA: `f89e55b7a564c8168565d46d5276bf5a9d9e1c66`; event: `pull_request`.
- Standard MCP caller, private X.Org Xvfb, injected 8 s XTEST delay after the initial synthetic `a` press, with the owner blocked in real `python-xlib Display.sync()`; synthetic app only.
- The raw JSON, observation PNG, run metadata, and complete X11 job log are preserved as captured. `SHA256SUMS` binds all four files and this report.

## Result

The observation confirms `a` was down and the owner had entered `Display.sync()`. Cancel returned in 1,004.5 ms with `owner_process_retired=false`, `owner_process_exitcode=null`, client disconnect `unknown`, and release `not_attempted` because the owner had not been confirmed retired. The integration test failed at the immediate-cancel owner-retirement assertion. It kept `release_confirmed=false`, cleanup `UNKNOWN`, task success `null`, replay disabled, and `late_server_request_possible=true`.

During failure teardown, a later close fallback did retire the owner by SIGTERM; a PID-qualified XRes observer then confirmed disconnect in 45.1 ms. That fallback's separate release worker returned `readback_verified` in 345.3 ms with empty `keys_down` and `buttons_down`. This shows the expanded worker window can complete the fallback release on this run, but it is not the cancel result and is not an independent post-cancel parent readback. The run does not establish cancel-path bounded release, task success, or the complete required readback sequence.

## Disposition

Keep this distinct `FAIL` next to the previous runs. The worker-window change is not sufficient: the next discriminator is why immediate cancel returns before owner retirement while close fallback later observes SIGTERM exit, and how to make the entire retirement-plus-release sequence return within the caller's bound. Do not infer success from fallback cleanup or rerun this same source/condition as a substitute for fixing the retirement boundary. No WSLc allocation was used.
