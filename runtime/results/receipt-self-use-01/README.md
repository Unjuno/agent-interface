# Receipt view: actual assistant use

The assistant started the documented `event_socket_v11` / `interactive_v27`
candidate on private Linux/X11, viewed the blank XTerm screenshot, selected
`text("t991071"); key("Return")`, and viewed the resulting saved-state screenshot.
The independent scorer returned exactly `t991071`; terminal input release was
verified empty, and the socket server exited 0 after the explicit finish command.
The action exchange took 366.561815 ms on the caller's clock. This is one simple
self-use example, not a human-speed or matched performance comparison.

During use, the full prepared-exchange report exceeded the chosen outer tool
output budget and was truncated. The persisted report remained complete. The
new opt-in `python -m runtime.cli_v1 receipt --report ...` command was then used
on that same real report. It preserved the successful independent evaluation,
terminal release, latest full observation, report metadata and all nonroutine
events while moving four routine/history records out of the default view.

Using the same compact JSON serialization, the report is 8,076 bytes and its view
is 5,338 bytes. These are serialized-byte counts, not measured model tokens or
latency savings. The raw report stays accessible via `--raw`; intermediate
observation history must be retrieved when relevant to the next decision.

Evidence:

- `runtime/`: raw events, deliveries, source identities, owner events and images;
- `exchange/`: exact preparation, request, complete reply and complete report;
- `view.json`: the actual compact view of the original report;
- `SUMMARY.json`: scoped observations and counts;
- `SHA256.json`: file hashes recorded before this README was added.

Absolute paths in the raw receipts are historical and have not been rewritten.
The copied images are under `runtime/`. Re-reading the copied report changes the
view's source path, so its serialized size need not equal the original 5,338 bytes.
This example does not promote the research runtime or verify long-session,
recovery, cross-domain or live-stream behavior.
