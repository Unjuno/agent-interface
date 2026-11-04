# App Server late usage after timeout and score

## Implemented seam

A timed-out `AppServerPublicMcpModelCall` can expose an opaque, same-turn usage source. The recorded caller first durably records the original timeout, captures an atomic notification/journal boundary, and returns without calling public MCP. A separate `observe_late_usage` operation is allowed only after the independent task-score event exists. It waits only for `thread/tokenUsage/updated`, records each cumulative update with both a normalized receipt and the exact App Server JSONL line, and never consumes `turn/completed` or replays its answer.

The client now writes its journal in binary mode so offsets are true byte offsets. Incoming journal writes and notification visibility share a lock order, allowing the caller to mark an unambiguous post-terminal byte/cursor boundary. The ledger verifies the raw App Server method, turn identity, counters, identity metadata, and SHA-256 references during reconciliation.

## Deterministic composition result

The new test uses a synthetic App Server journal and a rejecting fake public Relay. It writes one partial and then one final cumulative usage update after timeout and score custody, with a stale `turn/completed` answer between them. Assertions show:

- the generation remains `timeout`; the public Relay receives no request;
- usage cannot be observed before task-score custody;
- both late snapshots and both exact source lines are retained in order;
- the independent synthetic score remains true;
- the attempt count remains one and final token totals are counted once (21 input, 4 output);
- mutating a retained source line causes reconciliation to reject its digest.

This is an accounting and no-replay control-path test. It does not establish a real GUI effect, live provider behavior, or independent scoring quality.

## Verification

| Suite | Result |
|---|---:|
| client + App Server adapter + recorder, normal | 29/29 pass |
| same focused suite, `-O` | 29/29 pass |
| dedicated timeout/partial/final integration, normal and `-O` | 1/1 pass each |
| existing spool worker + public MCP composition (Fake X), normal | 22/22 pass |
| two Calc cases failing in full discovery, isolated together | 2/2 pass |
| full 11-module discovery with repository root on `PYTHONPATH` | 104 tests; 2 unrelated Calc timing/anchor failures |

The failed full-discovery and import-path attempts are preserved as failures; no acceptance conditions were changed. The focused logs and exit codes are adjacent. All evidence in this packet is synthetic/local.

## Remaining boundaries

- `app_server_spool_worker_v1.py` still closes the client immediately after timeout; its file-spool path does not yet publish a late-usage sidecar.
- No live model/provider or billing receipt was observed.
- No actual Fake X task-effect trial, WSLc run, MAP01 run, matched efficiency comparison, or performance frontier measurement was performed.
- The integrated-late-usage test has no real user interaction; the fake Relay rejects every request.
