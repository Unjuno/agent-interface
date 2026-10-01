# Composed exchange: actual assistant use

One private Linux/X11 XTerm session, seed 991072. The assistant viewed blank
frame 1, deliberately entered `draft`, viewed frame 2, then selected Ctrl+U,
`t991072`, Return. Viewed frame 5 showed the saved text. Independent evaluation
returned exactly `t991072`, both completed programs verified empty key/button
release, and explicit finish closed the server with exit code 0.

The first development attempt failed: the adapter combined `action_id` and
`read_request_id`, which the real cursor rejects before command dispatch.
`rejected-attempt/` retains its exact request, error reply and original report.
A command-free read at cursor 4 returned no subsequent events. After checking
the server's validation-before-write path, the assistant removed the conflicting
action scope and deliberately continued the same session with a new program.
No input was automatically retried. Tests now invoke the real cursor validator
inside the fake transport to catch this mismatch. The earlier report's missing
error message also motivated propagating server rejection into `needs_review`.

Each corrected action used one Python call with inline steps. The adapter
handled two socket exchanges (clock, submit), preserved the viewed delivery,
and retained requests/replies. There is no measured token, model-latency or
human-speed improvement here. The draft/correction was deliberately chosen
to exercise two decisions; it is not a recovery benchmark or product completion.

Evidence: `runtime/` contains untouched runtime files; `draft/` and `submit/`
contain corrected exchange artifacts. Top-level files contain initial read,
reconciliation and cleanup receipts. `adapter-source/` is the corrected tested
adapter and tests; it is not represented as the exact source of the first
failed attempt. `runtime/sources.json` records runtime identities.
`SHA256.json` covers all evidence files present before this README.
Historical absolute paths in raw records remain unchanged; copied images are
under `runtime/`. All five focused tests passed on Windows and WSL Linux.
