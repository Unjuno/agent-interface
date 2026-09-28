# Persistent host client for the native relay

`native_relay_client_v1.mjs` packages the primary assistant's previously ad hoc Node bridge to `native_mcp_relay_v1.py`. It selects no actions, changes no MCP result fields and introduces no inference or sensor. It requires a persistent Node-capable host; ordinary direct MCP clients can continue using the Python MCP server.

Create one client with an explicit executable, argument array and new evidence directory (whose parent already exists):

```js
const { createRelayClient, presentRelayResponse } = await import(moduleFileURL);
const client = await createRelayClient({
  command: 'wsl.exe',
  args: ['-d', 'Ubuntu', '--cd', '/absolute/repository', '--exec',
    'env', 'PYTHONPATH=.:research/live_control', '/absolute/venv/bin/python',
    'research/live_control/native_mcp_relay_v1.py', '--',
    '--run-directory', 'results-local/explicit-existing-run/run'],
  evidenceDirectory: absoluteNewEvidenceDirectory,
});
const result = await client.send('native_observe', { stage: 1 });
await presentRelayResponse(result, {
  text: value => nodeRepl.write(value),
  image: value => nodeRepl.emitImage(value),
});
```

For a new managed allocation, replace the explicit existing-run arguments with the managed server arguments documented in NATIVE_MCP.md. A client connection does not itself start that allocation. Images from native_observe are retained historical captures, not a new observation. Full text and image content remain in the same host response.

If host waiting is interrupted, retain the client and use `await client.wait()` to receive the same promise/result. Do not call send again as a retry. Only one request can be outstanding. Relay refusal can leave its next ID unchanged; the local attempt number still advances, so a later explicit corrected request cannot overwrite the refused attempt. An ambiguous server result must be reconciled using the existing native status/exact-request resume contract, not interpreted as no input. An exited client never respawns its process.

Requests are persisted before pipe submission. Raw replies are persisted before delivery. Existing evidence directories and nonfinite/omitted JSON values are refused. Protocol identity mismatch, process failure or persistence failure blocks further sends. No crash-proof fsync or power-loss durability is claimed. Data written to the pipe before failure may have executed; no retry is automatic. If the entire host process is lost, the in-memory promise is lost; reconcile retained evidence rather than reconstructing and replaying it.

Call `await client.close()` only after requests settle. This closes transport stdin and waits for transport exit; it does not send finish or certify GUI cleanup. Managed sessions still require explicit finish or opt-in native_stop as appropriate. A hung child may keep close pending. Returned content is not compacted further: existing Python receipt projection remains responsible for lossless references, and the full raw response remains authoritative.

Validation: `node --test research/live_control/test_native_relay_client_v1.mjs`. Eight tests exercise interrupted waiting, single submission, exact text/image forwarding, request snapshotting, refusal-ID reuse without evidence overwrite, process loss, response mismatch, directory reuse and invalid JSON values. Windows Node's test CLI did not resolve the WSL UNC test path here; copying the two exact source files into a fresh Windows temp directory passed. The native CI workflow also runs the tests with Node 22 on Linux.

Local real-MCP checks on 2026-09-28: list_tools then native_stop on an unstarted managed allocation returned not_started, with relay exit 0; no GUI allocation was created. A separate read-only attachment retrieved stage 6 from native-node-relay-02 and presented its retained 835/780 Calc image alongside the unchanged text, then exited 0. Records are in results-local/native-node-client-contract-01-evidence and results-local/native-node-client-retained-image-01. This is a transport integration check, not a new task benchmark or token/latency comparison. The preceding live self-use is retained in runtime/results/native-node-relay-01.
## Explicit review attribution

For public guarded responses, record the review only after viewing its image:

```js
await recordRelayReview({
  replyPath: '/absolute/transport/reply-21.json',
  receiptPath: '/absolute/fresh-review-21.json',
  task: 'task-4', phase: 'entered', reason: 'Caller reviewed the entered value.'
});
```

Import `recordRelayReview` from `native_relay_client_v1.mjs`. Use the exact reply
file selected for this review, never a mutable latest-source variable. The helper
records retained reply, image, call and source identity; it does not view the
image or certify semantic correctness. Existing receipts cannot be overwritten.
Missing images, ambiguous sourced reports and uncertain transport results refuse.
No receipt is automatically created when a response arrives.

The relay can launch the public server with `--server-kind public` and optional
`--runtime-archive /absolute/runtime.pyz`, followed by `--` and public server
arguments. Default native mode is unchanged. Select `--session-mode guarded-x11`
explicitly for the scoped tools. A terminated WSL session cannot reuse its old
aliases or connection; preserve it and allocate a fresh trial.

For opt-in same-host ordering and timing boundaries, use the [ordered host timeline](RELAY_HOST_TIMELINE.md). It serializes explicit presentation/review with sends and distinguishes callback completion from caller review; it does not measure model ingestion or semantic understanding.
