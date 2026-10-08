# Pending container reproduction request

This file is a request/protocol record only. It is not a lease or authorization.
No Docker/OrbStack inspection or launch is permitted until #5085 assigns this
exact allocation and confirms the current main, image digest/platform, owner,
and non-overlapping bounded window.

- Issue: #5413, bounded trace-buffer overflow T0.
- Allocation requested: `TRACE-ENFORCER-BUFFER-OVERFLOW-5413-T0-DOCKER-01-20261001`.
- Latest main at last refresh: `5a22b42f0d851d0d4549d197d37680d550b709df`.
- Candidate branch HEAD at last refresh: `5a8c4acdaab0548651a0470ff0ea5d8c0715b682`.
- Requested image, if already present: `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, `linux/arm64`.
- Requested resource envelope: network disabled, CPU 1, memory 512 MiB; no GPU/model/GUI/input.
- Requested window: 2026-10-01 16:15:00–16:30:00 UTC; request only, no access is inferred.

Candidate sources remain the exact frozen files/hashes in `PLAN.md`; the
one-shot runner and independent-audit command are in the #5085 queue request
comment. If main, source, or image identity changes before assignment, STOP and
refresh the complete freeze before any invocation. If the image is absent or
does not match, STOP without pull/build. Do not retry the candidate.

The prior host result is separately labeled `PASS_CONSTRUCTION_ONLY_HOST` in
`REPORT.md`; it must not be substituted for container evidence.
