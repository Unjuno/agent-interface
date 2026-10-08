# Issue #3311 Docker Desktop replay re-audit

This additive record independently replayed the already-published deterministic compiled-GUI mechanics probe and compared its complete generated report with the GitHub report blob. It is a preservation/reproducibility check, not a new preregistered allocation and not Issue #3311 acceptance.

- Source files match the three Git blob IDs and SHA-256 values recorded in the original replay README.
- The probe ran once in Docker Desktop desktop-linux, offline, with read-only source/root, 0.25 CPU, 512 MiB and 64 PIDs; exit 0 and the expected success marker.
- The replay emitted 15 scenarios and four rejected invalid-interface controls.
- The 75,579-byte replay report is byte-identical to public Git blob a674b924350bf8ff05e41f1007d2df4be1700fab, SHA-256 abef335e3949476510e083b5692e95edec5c971818c44ae9232d943fd315db36. An independent second container verified the byte comparison, parsed structure, counts, controls and source digests; zero audit errors.
- Three pre-scenario Docker setup stops are retained in AUDIT.json; none invoked the probe scenarios and none were pooled.

The report remains a synthetic test-double check only. No model/provider, X11, Chromium, user input, latency/token savings, amortization or live task efficacy was tested. The #3311 cold/warm/invalidation/repair comparison and meaningful-benefit decision remain outstanding.
