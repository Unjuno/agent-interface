# SIGINT, write-fault journal and pending-exit verdict successor

Pasteur review at f9a793ae8 confirmed pinned-byte loading and the unstarted-
reader repair, but NOT READY: signal masking did not cover the reader worker;
row/checkpoint filesystem write errors escaped without an independent durable
row; final summary could say PASS while process subsequently exited on pending
SIGINT.

Successor2a3abf050 blocks SIGINT in the reader worker as well as during main-
thread cleanup/finalization. CLI journals each full cleaned row to stdout before
writing the row file; a storage error preserves that JSON in Docker's external
logs and the nonzero Engine exit prohibits saved-only PASS audit. Construction
injects a row-file OSError after journaling and verifies exactly one row and
nonzero exit, with no false summary. This fallback requires the external
container log/exit receipt and is not an on-volume SUMMARY guarantee if storage
fails. Signal control sends SIGINT immediately after row write: complete row and
STOP checkpoint persist before the pending signal is restored.

Producer summary no longer claims PASS. It records
FOUR_CELL_GATES_TRUE_AWAITING_EXIT. Custody interprets a bounded result only
when container native exit is zero AND the separate saved-only auditor succeeds;
the Engine exit/receipts are external to the producer summary. README construction
history's old PASS label is explicitly marked historical. Audit fixture/schema
uses the new pending-exit literal.

Host suite20 PASS2.637s. Owned Docker f03-final-pass-gate-v1 20 methods
-B -O -W error PASS2.527s; 2026-10-04T00:06:32.609542384Z–00:06:35.523543552Z,
exit0/noOOM. Image560af28c711a2bf94cf9bedef4f5e47b26f86ea5bc79211c603addb74237540b.
Host/guest/container archiveSHA256 matched
0da02d0d0e90ff08aa90d6f02b1420ff8f272f61dab7162dc90bd75ef1059ee6.
Networknone, readonlyroot+input/tmpfs, UID501; resource limits configured,
not empirically read during this run. Raw methods/FINAL-PASS-GATE-v1.log.

PASS_CONSTRUCTION_ONLY. Formal producer0, official auditor0, model0. SIGKILL,
kernel/power loss, simultaneous external container-log failure and storage
failure remain outside producer's catchable evidence. New code/failure policy
needs independent review before formal allocation. No consumed experiment replay.
