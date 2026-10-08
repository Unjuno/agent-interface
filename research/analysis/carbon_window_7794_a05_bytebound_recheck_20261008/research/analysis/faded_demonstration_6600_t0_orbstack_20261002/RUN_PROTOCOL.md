# One-shot T0 protocol

Allocation: `FADED-DEMONSTRATION-6600-T0-ORBSTACK-20261002-01`. Current-main source freeze, exact hashes and commands are in `FREEZE.json`. Construction tests run before freeze; formal counts at freeze are candidate=0, auditor=0, retries=0.

Use cached `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`. Candidate container is network-none, read-only-rootfs and mounts only `candidate.py` and public `fixtures.json` read-only plus a fresh writable raw output directory. Candidate invocation is exactly once. Only if exit 0, invoke one separate network-none/read-only-rootfs auditor container; mount source/oracle and raw read-only, audit output writable. Never retry or repair after a formal invocation. If either invocation fails, preserve first outcome and STOP. Do not touch shared containers.

Candidate command: `python -B /candidate.py /fixtures.json /out/candidate.json`.
Auditor command: `python -B /src/auditor.py /src/fixtures.json /src/oracle.json /raw/candidate.json /out/audit.json`.
