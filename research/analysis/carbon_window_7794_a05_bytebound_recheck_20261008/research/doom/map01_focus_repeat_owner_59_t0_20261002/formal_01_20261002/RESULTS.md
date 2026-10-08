# Formal result: ISSUE59-FOCUS-REPEAT-OWNER-T0-20261002-01

## Decision

`PASS_OWNER_FOCUS_RELEASE_SCOPED` — one bounded CPU/Xvfb trial on WSLc. The independent auditor exited 0 and reconstructed the classification from the immutable raw record. Candidate/auditor/retry counts: **1/1/0**.

This pass is limited to the private Xvfb/XTEST mechanism and the exact current InputOwner v10, executor v3, and lease source blobs recorded in `FREEZE.json`. It does not close Issue #59's live threat-exposure/MAP01 gate and does not establish real-desktop, application, gameplay, GPU, or general reliability behavior.

## Evidence

- Frozen main: `a5756d9b31231a4d64268610236622ac44c36f1f`. The three expected source Git blobs and SHA256 values matched the raw record.
- Pinned image: `focus-repeat-59-t0:20261002`, image ID `sha256:865bfbcc86992769ec9b8311a2344b67c664639d96d7cf0d5c407df9c2c500ed`; pull disabled and network disabled for both processes.
- Candidate exit: 0; raw file: `candidate/raw.json`; SHA256 `88614e920a1ad68b358431d39e4abb1964433828086236f3b235ea25acb8d250`.
- Independent auditor exit: 0; classification: `auditor/classification.json`; SHA256 `022c0bdbcbe2d124e6692e27d078fed18210e3d5ba1bcae54a863a89e7fed80`.
- The repeat control observed four matching A KeyPress events and verified the key was up afterward. Xvfb exited 0; its socket and lock were removed.
- The B reader subscribed on the same connection it drained before the focus request, completed XSync and final drain without exception, and covered through after owner release. It observed a B KeyRelease and **zero matching B KeyPress** between focus request and verified release.
- Owner focus readback observed B; the owner's `focus_changed` release reported `verified: true`, `verified_empty: true`, and `keys_down: []`.

Measured monotonic boundaries (nanoseconds): focus request `50115621471`; requester XSync return `50115708898`; external focus readback `50115807609`; owner verified release `50116131703`; final event-pump stop `50217298315`. The sole B event was a KeyRelease at `50116290191`, after release verification. No ambiguous late B KeyPress was dequeued.

## Limits and retained runtime note

The Xlib owner-focus tracing proxy can perturb scheduling, this is a single trial, and event times are host receipt times. The preregistered auditor treats a matching B KeyPress dequeued at or after release as HOLD. WSLc warned that cgroup/swap memory enforcement is unavailable; the requested 512M is not claimed as effective. This event-order experiment is not GPU-compute-bound, so no GPU was used.

Exact commands are in `COMMANDS.txt`. Process stdout, stderr, exit codes, raw evidence, classification, and their checksums are retained in this directory.