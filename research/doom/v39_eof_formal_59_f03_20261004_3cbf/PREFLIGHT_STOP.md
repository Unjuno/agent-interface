# Source-preflight STOP retention construction

RED source 655735dab: real empty temporary package directory caused
FileNotFoundError to escape; test assertion failed: preflight source failure
escaped without a saved STOP. No mock subprocess or mock filesystem used.
Successor 72d3c6d19 retains SUMMARY.json with STOP_PREFLIGHT_SOURCE,
empty cases, FileNotFoundError type, error detail, retries0/model_calls0;
returns1 before any cell. Test requires exactly SUMMARY.json in output.

Host package suite 8 PASS (0.010s). Owned isolated Docker
f03-preflight-stop-v1: 8 PASS (0.003s), python3 -B -O -W error.
2026-10-03T23:28:05.536554312Z–23:28:05.805335372Z,
exit0/noOOM. Image sha256:560af28c711a2bf94cf9bedef4f5e47b26f86ea5bc79211c603addb74237540b.
Host/guest/container Git archive SHA256 matched
92a1376d5c8c6f7e8f1268cad7add04f4c0b34230195a1b5f5071075746a605f.
Network none; read-only root/input; tmpfs; UID501;
configured CPU1/memory1GiB/swap0/pids128 (not measured cgroups here).

PASS_CONSTRUCTION_ONLY. Formal native0/official auditor0/model0.
This exercises actual runner preflight and file retention, not a malformed
pipe handshake after a child starts. Source mismatch/archive corruption
branches and output-write failure are not separately executed here.
No consumed experiment replay or historical result change. Repository-wide
suite not run. Still requires runtime first-cell STOP orchestration controls,
receipt/export/source custody and independent prelaunch review.
