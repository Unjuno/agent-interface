# Development notes

- Reused the retained PR #280 decision structure (URL + RuntimeUID + text + observation age + UNO->XID binding + final active/focus equality + Writer Ctrl+End insertion-point reacquisition) without modifying that namespace.
- Development unit tests: 5/5 PASS.
- Six development sessions all passed the proposed durable gate.
- `fresh`: accepted, 28 XTest events, in-memory A and post-exit ODT A both `bookkeeperoffice`; B `bookk`.
- `stale_uid`, `wrong_doc`, `focus_drift`, `stale_age`: zero recovery events and durable A=`book`, B=`bookk`.
- `text_changed`: zero recovery events, refusal `STALE_TEXT`, durable A preserves injected `boox`; B remains `bookk`.
- UNO `store()` is deliberately classified as test-fixture persistence after the measured recovery/refusal, not the text-delivery route and not evidence that Ctrl+S targeting is safe.
- Formal conditions are frozen after this calibration; no development row is pooled into formal evidence.
