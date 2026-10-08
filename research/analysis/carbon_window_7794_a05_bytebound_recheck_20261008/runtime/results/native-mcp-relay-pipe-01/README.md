# Primary relay use with byte-preserved output

The primary assistant sent three explicit JSON-line requests on one persistent
relay: start, submit and status. Linux redirected relay stdout directly to a
fresh JSONL file, so Windows terminal redraw never touched the response bytes.
A read-only helper returned a complete response by ID; orchestration forwarded
its exact text/image blocks. The assistant viewed both images and authored the
move/save action after viewing the initial image and goal.

Inkscape seed 991121 saved x=86, y=50, width=40, height=30 with no transform.
One program emitted 43 operations; release was verified empty, cleanup reported
completed and owner 17936 returned terminal/code 0. EOF closed relay exec 56521
with code 0. No per-decision file was created, though the harness still publishes
its immutable request. The response JSONL file and explicit read calls remain.

SDK submit took 854.916 ms, with 842.875 ms inside the exchange. This single
ordered trial does not establish latency or model-token improvement. Host
presentation, interpretation, disconnect recovery and multi-stage work remain
unmeasured here. The prior failed PTY trial remains retained separately.

Run `python3 runtime/results/native-mcp-relay-pipe-01/audit.py`. It verifies 44
manifest files, three response IDs, exact MCP image bytes, immutable request
identity, saved SVG geometry, release and owner exit. The manifest includes the
audit script, but predates this README. PLAN.md was written before allocation.
relay.py captures the source used, including pre-start terminal-output refusal.

Archive deviation: the Windows-written shell script had CRLF endings and created
the stderr filename with a trailing carriage return. Its original bytes were
copied to stderr.log in this archive; provenance records the original name.
The original launch.sh is retained unchanged. Use LF when reproducing shell
scripts. This artifact-copy issue did not affect response JSONL or GUI input.
