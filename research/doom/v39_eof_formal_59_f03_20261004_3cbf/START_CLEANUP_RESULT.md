# Unstarted reader STOP retention construction

RED85c161955 reproduced RuntimeError cannot join thread before it is started,
escaping cleanup before STOP row/SUMMARY. Real Thread/child/pipes/filesystem;
only Thread.start boundary fault injected with KeyboardInterrupt because
external signal timing cannot deterministically hit this boundary. Assertions
check actual saved rows, SUMMARY and actual reaped-child/retired-reader states,
not mock outcome. No claim this is a real SIGINT allocation.

Successor54e8f1282 checks ident before join, retains cleanup exceptions and
KeyboardInterrupt, separates terminate/wait/kill fallback so cleanup failure
does not immediately skip later steps; summary adds cleanup_fault reason.
First injected start interruption retains baseline row and SUMMARY, empty
cleanup faults, child and never-started reader nonalive. Host16PASS0.886s.
Other newly guarded cleanup interruption branches are not separately fault-
injected here; do not promote them to fully verified cleanup recovery.

Owned Docker f03-start-cleanup-v1 16methods -B -O -W error PASS0.869s;
2026-10-03T23:49:22.201478176Z–23:49:23.438393351Z exit0/noOOM.
Host/guest/container archive5b1aeaae8d214062dde0909512898fb6e5e2068802f37d40a0b5db2f6c8f96a5 matched.
Raw log under methods/START-CLEANUP-v1.log. Image560af28c711a2bf94cf9bedef4f5e47b26f86ea5bc79211c603addb74237540b;
networknone/read-onlyroot+input/tmpfs/UID501; configured CPU1/1GiB/swap0/pids128,
not empirical resource observations in this run. Repository-wide suite not run.

PASS_CONSTRUCTION_ONLY; formal0/auditor0/model0. Source-import execution identity
Important still unresolved; independent successor verdict and frozen custody
required. Old outcomes/archives immutable. No formal replay or adoption claim.
