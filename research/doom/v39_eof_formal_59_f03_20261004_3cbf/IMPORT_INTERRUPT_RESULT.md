# Guarded dependency and SIGINT construction successor

Fresh-process RED491dca272: missing candidate import exits without SUMMARY.
Real SIGINT RED24227e933: child observed before SIGINT; uncaught
KeyboardInterrupt exits -2 without terminal summary. Successor de4a4969a
moves imports after hash validation inside saved preflight guard, catches
KeyboardInterrupt at preflight/measurement boundaries, retains fatal_type
and summary stop_reason after cleanup. Does not catch SIGKILL or repeated
interrupts inside cleanup; these require external custody retention.

First three distinct container construction failures remain unchanged:
v1 de4a4969a, archive be710299f055744141d2a7b66c22476ad7e87d4ec04b87df786bf37b1c5c59dd,
23:40:30.597073268–23:40:31.542370615Z exit1: ps unavailable.
v2 729321be2, archive 7f18f137b6a70624413572f249ae921cb6d38cf4a64c4e2ffe4bd7d236d7f170,
23:41:05.142874384–23:41:06.132121572Z exit1: interrupted before reader
creation, cleanup_reader_alive=None not False; source correctly distinguished absence.
v3 abc5b32b0, archive 3780af3c5ac50fe66b07443f8e464964fa10bd730264bb026a7056414b6d2c66,
23:41:38.668779446–23:41:40.556538675Z exit1: cannot externally observe
already-retired EOF reader task. No production change between v1–v4.

v4 e8566ede6 uses Linux /proc child listing (macOS ps fallback), observes
actual child before SIGINT, accepts explicit absent-reader None or retired
False, requires child retired/cleanup faults[]/saved first-cell STOP reason.
It does NOT prove interruption while reader is active. Fifteen methods
-B -O -W error PASS0.737s in owned Docker f03-import-interrupt-v4,
2026-10-03T23:42:22.305475853Z–23:42:23.322994359Z exit0/noOOM.
Archive84801f15e7cef4ae7401a5c838c771e9fdaf79da202a84c065324c2ffd57c275
matched host/guest/container. Raw all-four logs retained under methods/.
Image560af28c711a2bf94cf9bedef4f5e47b26f86ea5bc79211c603addb74237540b;
network none/read-only input+root/tmpfs/UID501; configured CPU1/1GiB/swap0/pids128,
not empirical resource reads here. Host de4 suite15 PASS0.837s before Linux
observer changes. Final host observer revision not re-run here.

PASS_CONSTRUCTION_ONLY; formal native0/official auditor0/model0. No replay of
consumed allocation. Old failures never relabeled. Import loading still needs
independent successor review; cached modules and corrupt dependency branches
not separately qualified. Full custody/freeze review remains outstanding.
Repository-wide suite not run; no adoption or full-lifecycle claim.
