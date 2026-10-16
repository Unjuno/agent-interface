# Native request write before response deadline — #59

The current synchronous client writes a request before creating its response
deadline. One new ordinary native Windows construction observes a262144-byte
ASCII request blocked at actual source `_write:48`, with request at67 and no
deadline local at the fixed250.3702ms checkpoint. Only private inert-peer
release permits the caller to finish with BrokenPipeError at261.0279ms.

| One actual cell | Caller result | Parent-clock duration |
|---|---|---|
| Healthy large reader | Exact262144-byte payload result/hash | 3.6624ms |
| Unread small5-character request | TimeoutError | 69.5357ms |
| Unread large262144-character request | Still blocked at checkpoint; BrokenPipeError after fixture release | 261.0279ms total |

These are one descriptive sample per cell, not medians or an upper latency
bound. The request argument is50ms; no response deadline has been created in
the blocked cell, so its internal deadline is not described as overdue.
All3 native peers exit0; source reader and caller stop; all owned parent
stdin/stdout/stderr close. No terminate/kill fallback occurred. The artificial
fixture reads no stdin in the two unread cells and grants no action authority.

Source freeze: main9c0692dabbfc7fc2fa5bd111b6de4baee578800d,
research/live_control/codex_app_server_client_v2.py6303B,
blobbbfad463d7428dd80b7dca533d518a77604e69f1,
SHA8ed4e3496ef8154d3c4573fb1386efe6e036292a3809e43aa37fc22aecc5b42b.
Initial claim/source annotationdd6f is retained; only6896 evidence intervened
before freeze, client bytes unchanged and zero children had run. Windows11
build26300/CPython3.12.14, native real pipes/threads, journal disabled, ASCII
input and fixed0.05s request/0.25s checkpoint/setup1s/cell3s conditions.
Actual driver07:43:44.201764–07:43:45.229650UTC exits0. Original raw SHA
da49adabbfbde3afba302526fc777a3338ddf9533b0d20d344185087eaec3033,
freezeeba2a2bcacdba9fd09e3b6e10ff91d777ed6ac2f3206642004190331f709228a.

Frozen separate saved-only auditor passes the source-stage/control/endpoint
witness and rejects16 effective copied corruptions for their intended reasons,
without native/source/producer replay. This exercises the stated fields and
consistency, not authenticity or resistance to coherent fabrication.

Popen text stdin translates LF to the OS line separator; the healthy captured
CRLF wire matches the planned native bytes exactly. See [Python3.12 subprocess
documentation](https://docs.python.org/3.12/library/subprocess.html). Microsoft's
[CreatePipe documentation](https://learn.microsoft.com/en-us/windows/win32/api/namedpipeapi/nf-namedpipeapi-createpipe)
describes blocking synchronous pipe writes. Those source facts support the
construction design; our checkpoint/cleanup evidence is from the actual run.

This archive changes no runtime, default, workflow, dependency policy or
navigation index. Original helper source is quoted as `.py.txt`, and binary
wire snapshots are data. Package-local attributes preserve exact bytes and
allow CR line endings; source/checksum/manifest maps bind every public file.
Only private filesystem spellings in metadata are projected; original/public
lengths and SHA remain separate. No missing private bytes are imputed.
`public_qualifier.py.txt` independently qualifies the projection links and
reconstructs the original saved-only endpoint oracle on public data. Its
metadata-only view replaces only the verified original-freeze hash link with
the public projection hash; raw files, source/input/gates/endpoints are unchanged.
It never imports or executes the client/native producer/peer.

EOF diagnostics remain with51-d447/#6945, response-ID/cache with222f/#6952,
startup/journal-lock withb04b. No source repair competes here. This result
isolates a separate pre-deadline write recovery boundary; it does not prove
whole-call recovery, physical effects/input release, real Codex/model/game
behavior, payload threshold, frequency, latency/token/resource benefit, or
close#59/#57. No model/provider/GUI/game/input/GPU/Engine/container/WSLc/shared
lease/formal allocation/main send. Review/application require normal FINAL-v5
nonauthor consensus/current-tree/live gates; publication itself is not adoption.
