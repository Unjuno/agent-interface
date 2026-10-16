# Owned service process: Fake X construction and retained evidence

2026-10-16; parent [#59](https://github.com/Unjuno/agent-interface/issues/59).
Adoption candidate: [explicit API](../../live_control/INPUT_OWNER_PROCESS_V3.md).
This closes the standalone process/receipt construction gap left by current RPC
v2. Standard backend selection, cancellation/telemetry and actual session death
remain unfinished; it does not complete computer control or qualify native input.

## Conditions and result

Windows, Python3.13.14; Pillow12.2.0, numpy2.3.4, python-xlib0.33, MCP1.30.0.
Real private sockets and explicitly owned spawned Python processes; all display,
capture, focus, identity query and input calls are Fake X. No WSL/container/game,
provider/model or real display/input operation. These are ordinary construction
regressions, not a replay or replacement of historical formal allocations.
The named guarded runner is preserved as `check_owner_process_v3.py.txt`; execute
the source driver with Python normally and `-O`, supplying distinct JSON outputs.
The original machine paths identify conditions, not portable installation paths.

Final `final-normal.*` and `final-optimized.*` each retain55 methods, zero failures,
errors or skips;13 process/inert rows plus26 existing RPC regression rows. Parent
and accepted child startup source hashes bind the loaded code; child optimization
is explicitly0/1. Expected injected child exceptions appear in stderr. All owned
services were joined without test crash fallback. `pid-absence.json` records a
read-only check of20 recorded owned child PIDs, all absent at that time; it is not
a permanent PID-reuse guarantee or authority to kill a process.

| Case | Discriminating result |
|---|---|
| normal / client death | Same owner releases and saves consistent receipts; distinct client exits73 without finally; service independently observes EOF and exits0. |
| service death | Service exits71 after press; no acceptable recovery/finish. Last Fake observation is press only; physical post-death input state is not inferred. |
| blocked release | Service remains alive/unverified; later settlement releases and exits0 but initial recovery bytes and failure remain unchanged. |
| context exit failure | Initially verified recovery alone cannot qualify failed teardown / exit1 / absent finish. |
| startup failure / partial allocation | No accepted startup or result; owned handle remains inspectable; acquired descriptors close even before Process construction. |
| publication failure during blocked release | Same service waits despite absent recovery file; after release it exits1 with diagnostic and no finish; failure never upgrades. |
| complete files before process exit | Receipt can be internally verified while service remains alive; parent result stays unverified until owned exit0. |
| generation / exclusive publication | Wrong generation, file replacement and reuse of output directory are rejected. |
| single-read snapshot / inert custody | Export hash joins exact read bytes; fatal/paired startup exceptions retain primary and handle; unresolved owner wait precedes context exit. |

`read_saved.py` imports no runtime, socket or process implementation. It validates
final row inventory, exact exported bytes/hashes, source pins, child modes,
identity/lineage, recovery/finish joins, initial failure retention, process exit,
Fake edge observations and cleanup. Nine altered-record negatives per mode are
rejected. `readback.json` is its retained output. The26 RPC rows are retained as
selected regression output; their full prior independent audit remains in the
[RPC v2 packet](../current_owner_rpc_v2_20261016/README.md).

## First outcomes and corrections

`exploratory/` retains earlier passes, source snapshots and first failures without
promoting them to final source qualification: missing implementation; export
text/newline ambiguity; changing-file hash/read mismatch; interrupted startup
custody; and allocation/publication faults. The latter red produced two errors
and one assertion failure before repair. Final tests include a real child process
for the overlapping blocked-release/publication fault, beyond the inert repro.

The early byte-export failing cell was not appended before temporary cleanup;
its raw is incomplete. Original reports are untouched. For other early retained
files, `owner-process-v3-original-hash-matched-raw-recovery.json` reconstructs
exact LF/CRLF bytes only when matching the originally recorded SHA256 (17 initial
pass files and13 byte-red files). It is saved-byte recovery, not experiment replay.
Historical r2/r3/r4 passes have older source pins; only final-r5 copies qualify the
published runtime. Test-only fsynced Fake edge logging is no production latency
measurement. SHA256SUMS covers packet members except itself.

## Continuation and repository organization

Keep the distinct unresolved question under#59: adapt the selected backend and
Executor to external-owner receipts/custody, parent cancellation and telemetry,
then actual controller/session death. The service library is usable construction,
not automatic default adoption. Old crash-owner ideas, original blobs and rejected
source-transfer behavior remain in the prior convergence packet. No new Issue or
reviewer quota is introduced, and no unfinished scientific Issue is closed merely
because its idea has been documented.
