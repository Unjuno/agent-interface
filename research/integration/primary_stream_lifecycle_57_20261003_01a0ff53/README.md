# Primary stream ownership through startup and termination

Refs #57 and Draft PR #6919. This extends the existing input-error repair with whole-owner error observation. The original v1 package, comparison, auditor allocation, proposal and first records remain immutable in the sibling `primary_input_error_57_20261003_01a0ff53` directory. None of those consumed executions was replayed.

`runPrimaryStdio` creates its real relay and writes ready before the inner line transport starts; it writes terminal after that transport removes its handlers. The old owner has no input/output error observer during those two intervals. Install temporary observers before relay creation, retain the first fault, observe the same host and accepted command, then remove only these owned observers after terminal handling. Do not replay a request or start a replacement host. The existing Readline Interface listener remains part of the repair.

## Actual first results

| Check | Actual result | Scope |
|---|---|---|
| Added three whole-owner regressions on old source | 17 methods, 14 pass/3 fail; process exit 1 | Ready input, ready output, terminal output unhandled errors |
| Same regressions after repair | 17/17; exit 0 | Existing Node stdio module, actual private zero-operation relay children |
| Four old-source native parent probes | exits `[1,1,1,0]` | Three unhandled failures and normal EOF control |
| Four candidate native parent probes | exits `[0,0,0,0]` | Original fault identity, host exit record, listener restoration; normal EOF preserved |
| Two additional candidate pending-command probes | exits `[0,0]` | One actual fixture request each; held original reply observed before owner cleanup; success and occupied persistence slot |
| Affected stdio/exchange/relay-host selection | 45/45; exit 0 | macOS 27.0.1 arm64, Node 26.7.0 |
| Saved-data auditor and semantic corruptions | exit 0; eight effective mutations rejected | Separate Python implementation, no producer/runtime import |
| Author-only composition with #6902 head `12e15aa7a3dc71a95f31ac7b600212c742dd9bff` | 20/20; exit 0 | Exact combined tree, no foreign source adoption or nonauthor vote |

All ten native construction parents have retained UTC, actual numeric parent exit, first stdout/stderr, fixture PID/start/typed exit records and the collector's PID-absence observation. The eight simple cases deliver zero relay request bytes. The two pending cases each have one actual peer request and original response, fixture exit 0, no pending work at exit, and no retry. Baseline parent failure is not converted into a pass because the data-collection wrapper itself exits 0. Baseline fixtures did exit normally, but the failing primary owners did not reach their owner summaries; fixture death alone is not proof of observed owner cleanup.

The pending success preserves the original host reply and the exchange's same reply plus its existing `attempt:1` enrichment. The occupied exchange reply slot stays byte-identical; the host's original response is retained, the correlated command-error row has `replay_allowed:false` and consumed `next_id:2`, and owner rejection preserves the original input fault.

## Retained construction failures and scope

The first saved-data auditor rejected a legitimate result because it omitted the exchange's existing `attempt` enrichment. Its source and exit-1 records are retained; only the auditor was repaired. The first #6902 composition export flattened the repository layout, so five child imports failed: 15/20, exit 1. A fresh export restored the original relative layout with identical production/test bytes and passed 20/20. Neither failure caused a native comparison replay or a production change.

Other worker `01a0ff58-7772-7312-9c2a-459f38d6734d` claimed a separately frozen accepted-command host/peer comparison in [comment 5965565727](https://github.com/Unjuno/agent-interface/pull/6919#issuecomment-5965565727). That 04:34:27 UTC claim was discovered after these pending construction checks. The pending-success context partly overlaps that work and is not an additional independent scientific contribution or a counted review. Our occupied persistence-slot control and whole-owner ready/terminal repair have explicit separate scope. Their owned comparison was not invoked, cancelled or reassigned.

These are ordinary regression constructions using the actual `runPrimaryStdio` API, real Node PassThrough/Writable streams and actual private fixture-relay processes. The public `--config` CLI, real OS stdin/device failures, a portable MCP server/backend, physical input/release/task effects, GUI, model, GPU, container runtime, other Node/OS versions, throughput and total task/token/time efficiency were not exercised. Write callbacks are responsive or explicitly released; this change adds no hard I/O deadline, global byte framing/resource bound, cancellation, retry, route/default or schema change. The fixture tool name `interface_clock` is synthetic and does not establish real backend callability.

Source commit before native green checks: `c870def76734444925b9ca244bdbbcd48a2d84a8`. Baseline: `dbe05f5ce33b6827dbd3d09e8a85da1e2d20f51a`. Author main composition used `316ac44b24d4ac29c1942d2fee51f1c0599855b1`; all five candidate module bytes and the original package stayed unchanged. This is preparation for review, not an application certificate. The changed head requires a new fixed proposal/committee epoch and renewed exact-content votes. No main update is included here.

## Evidence and safe inspection

`SOURCE_COMMIT.json`, `BASELINE_ID.json` and each prelaunch `SOURCE_FREEZE.json` bind source/dependency/helper bytes. `red`, `green`, `pending-green`, `unit-red`, `unit-green-01` and `checks` retain the actual first records. `PROJECTIONS.json` maps every changed public file to its unmodified private original SHA256 and derived public SHA256. Only exact owned-directory prefixes are substituted; embedded original channel hashes remain original hashes. No raw diagnostic whitespace is normalized. Narrow artifact attributes exempt only the retained diagnostic files that have trailing whitespace.

Saved-data inspection: `python3 -B audit.py .` and `python3 -B audit_controls.py` from this directory. These read retained data and use disposable copies; they never import/start the runtime, producer, fixture or consumed v1 allocation. The public projection was independently read back by both commands. Historical construction test module snapshots use `.mjs.txt`; `ARCHIVE_LAYOUT.json` preserves their source-path correspondence. This directory is outside the explicit native-mcp workflow paths and Node test selection; no workflow was added or modified.

`SHA256SUMS` covers every delivered package file except itself. `RESULT.json` names only the exercised checks. Original v1 approvals/reviews are historical and cannot be silently transferred to this new content.
