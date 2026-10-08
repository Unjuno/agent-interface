# E02 first result: PASS_CANDIDATE_READER_SIGNAL

Parent #59; predecessor E01 PR7220 unchanged. One candidate-only native producer,
one saved-only diagnostic auditor, retries0. E02-59-20261004-3CBF consumed: no
replay to upgrade scope or fill a missing field. Source freeze3069eae6715a0dedc27f2cea007b1f7c88cd666d
public MCP readback and prospective #59 comment5973098081 preceded launch.

| Cell | Actual wait outcome | Wait elapsed | Reader at checkpoint |
|---|---|---:|---|
| E02 healthy | ready | 9.469097 ms | alive |
| truncated JSON | _SessionReaderFailure; JSONDecodeError cause | 8.609263 ms | retired |
| ready then handshake/fault | ready, then _SessionReaderFailure; JSONDecodeError cause | 8.746513 / 0.082458 ms | retired |
| JSON [1] | TypeError | 7.571178 ms | alive |
| invalid UTF8 ff0a | _SessionReaderFailure; UnicodeDecodeError cause | 7.767011 ms | retired |
| clean stdout EOF, live peer | TimeoutError | 370.226284 ms | retired |

All six peers were alive at checkpoint, exited0 after owned stdin EOF cleanup;
all readers finally retired. No unhandled thread exception, fatal or cleanup
fault. PeerPIDs/PPIDs link to producer PID1/runtimeUID501. JSON cause retains
actual decoded doc `{"event":\n`; UTF8 cause object is actual `ff0a`. Ready-first
ordering and parent CONTINUE→fault emission are checked from saved monotonic
checkpoints. Reader join after fault before checkpoint is NOT part of wait elapsed.

Decision: conditional error-notification mechanism supported for tested receiver
faults without dropping prior normal events. This is candidate source qualification,
not production adoption, full-controller cleanup/recovery, natural-fault frequency,
default40-second behavior, hard deadline, game/model/input/task-effect success.
EOF and shape validation remain intentionally unresolved controls. Do not rank
E01/E02 latency: different inputs/order/conditions, no matched causal timing design.

## Source and runtime custody

Original currentv39 SHA256a0bcfa076970b7cf6d048155478952958280b7958e0bbe486c0f1f12a55e4f0e;
full inert candidate dca770e5e0c532b301b12032c9532bd5fae602947caff4fff21bde60634a57f1.
Only two literal sites differ (local exception class+reader catch; wait signal
raise before row indexing). Inverse reconstructs all original bytes including
historical final CRLF. The tested extracted class/reader/wait are literal candidate
AST, not a handwritten alternate wait. Main v39/peer6944/7084 sources untouched.

Native UTC2026-10-03T20:17:52.809814046Z–20:17:53.433003237Z, COMPLETE/exit0.
AuditorUTC20:18:01.820048756Z–20:18:01.893434862Z, exit0/PASS_SAVED_DIAGNOSTIC_AUDIT,
verdictPASS_CANDIDATE_READER_SIGNAL. Both terminal/OOMfalse/restart0. Python3.12.15,
same pinned image; own VM/Engine, CPU1/memory512MiB/swap0/pids64/nonroot501,
networknone/read-only root+source/capdropALL/no-new-privileges. Host not exclusive.

Fourteen native raw receipts retained exactly; auditor hashes those same parsed
byte buffers. Docker-cp export and direct host original/export copies are identical.
Execution pins checked before native and after audit. Nine construction methods,
including one peer-only EOF helper, are excluded from native six-cell allocation.
Original REDs, mixed-newline generator preflight failure, auditor bool alias RED,
EOF RED and corrected GREEN streams retained. No construction failure regraded.

Saved scorer independently specifies outcomes/causes/chronology/cardinality/types,
but trusts producer checkpoint fields rather than independently observing live
threads. Emitter receipts attest successful writes, not raw stdout readback. No
wrapper-wide mutation coverage: seven saved semantic controls tested. Cleanup
helper assumes actual PIPE handles; absent-stream defensive gap stays declared.

## Next integration decision

This package supplies complete candidate source, generator/inverse, methods,
executed evidence and closed hashes to the existing v39 startup/wait integration
owners. A nonauthor must compose those sources on fresh main, retain original
error/queued event priority, check actual main cleanup/adoption and applicable
ownership/content review rules before replacing production code. It is NOT
permission to overwrite6944/7084 branches or treat their votes as transferable.
EOF notification and shape-policy design need separate explicit successor gates,
not silently broadening this successful allocation. Full live #59/threat feedback,
MAP01, same-model efficiency and human-tempo roadmap remain unresolved.
Branches/VM evidence retained while freezes and worktree/dependencies reference
them; no deletion based only on PR closure/merge.
