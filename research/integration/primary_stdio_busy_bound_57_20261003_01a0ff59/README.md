# Primary stdio busy-response bound (#57)

This repair closes a concrete response-work gap in the existing primary entry path. The transport already admits one command, but previously retained one asynchronous `busy` response per rejected arrival. A real stalled Node Writable with 256 additional lines fails the bounded-work regression. The candidate stops intake before a second unfinished busy write, continues to observe the same committed promise and its result, and lets the original owner clean up its relay.

The three-line production guard and three focused regression methods are in `runtime/host_v1/`; its README documents the overload line's missing reply and exit-2 reconciliation. One observed busy response remains legal and can be followed by another after its write completes. A synchronous line burst may stop even with a responsive sink because callbacks have not yet been observed. This deliberately requires callers to await each result as the existing contract specifies.

## Retained checks

- [RED freeze](RED_FREEZE.json): exact baseline exports, test definition and finite stopping rule before execution. RED: two expected failures and one legal control passes. [Original RED](checks/red/stdout.txt).
- [Candidate/pipe freeze](CANDIDATE_FREEZE.json): exact source, probe and auditor identities before the one two-arm CLI block. [Baseline CLI raw](pipe/baseline/stdout.jsonl), [candidate CLI raw](pipe/candidate/stdout.jsonl), complete stdin, stderr, original exchange/host files and actual child exits remain under `pipe/`.
- Both real Windows child-pipe arms deliver the exact original committed presentation with one actual fixture-relay request and relay exit 0. Baseline produces two busy responses and normal owner exit 0; candidate one busy and error owner exit 2. No rejected command enters the exchange or relay. [Read-only v2 audit](checks/pipe-audit-v2/stdout.txt).
- New regression methods 3/3 pass; the existing shared Node workflow selection plus them passes 190/190. [Full check](checks/shared-suite-complete/stdout.txt). First sparse-source check retains 166 pass/one missing read-only timing dependency failure in [its original log](checks/host-suite/stdout.txt); exact committed dependency export then fixes setup without a source change.
- Committed-source distribution tests pass 9/9, including exact host-bundle export and destination-conflict refusal. [Complete log](checks/distribution/stderr.txt). Evidence-only whitespace attributes preserve the copied source's original CR byte and assertion-log spaces; [pre-repair check](checks/whitespace-pre-repair/stdout.txt) remains unchanged.
- Original [auditor v1](audit_pipe.py) passes original raw and rejects four corruptions but accepts boolean `attempt=true` for integer 1. [First control result](controls-v1.json) is retained. Separately versioned [v2](audit_pipe_v2.py) uses typed canonical JSON equality at the remaining scalar/sequence/exit checks. [V2 freeze](AUDIT_V2_FREEZE.json) pins unchanged raw before re-audit; [five controls](controls-v2.json) all reject. The primary/relay block was not replayed.

## Scope and reproduction

All checks are ordinary finite engineering on Windows x64, Node 24.19.0. No formal allocation, shared resource, physical input, GUI, model, GPU, Docker or WSLc was used. The relay is a synthetic text-only close responder. This evidence supports the local response/owner contract, not native release, task effect, efficiency or a #57 end-to-end result. `RESULT.json` preserves construction/setup failures and exact limitations.

From repository root with Node 22+:

```text
node --test runtime/host_v1/test_primary_stdio_backpressure.mjs
node --test research/live_control/test_native_relay_client_v1.mjs research/live_control/test_relay_host_timeline_v1.mjs runtime/host_v1/test_*.mjs
python research/integration/primary_stdio_busy_bound_57_20261003_01a0ff59/audit_pipe_v2.py research/integration/primary_stdio_busy_bound_57_20261003_01a0ff59/pipe
```

Read-only corruption reconstruction accepts a fresh output directory. Do not point the probe at occupied output paths; its two original executions are complete. Baseline/candidate source exports, prospective freezes and complete command stdout/stderr/UTC/exit receipts are retained; all evidence files are byte-hashed in `SHA256SUMS`.

No main application has been attempted. Fixed before-vote nonauthor content approvals, an exact current-main combined-tree check, actual GitHub requirements and one conditional application remain separate gates. Common fleet deadline/N are unavailable and were not reset.
