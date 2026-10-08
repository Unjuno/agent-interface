# Recovery review — Issue #4066

This file records a byte-preserving recovery of the abandoned remote branch
`research/sealed-sequential-pagination-20260922` at `67862eab4000110c7c28ea55d1fbe711262fb7c1`.
The original report, frozen gate, STOP receipt, candidate source, and eight
evidence parts are retained unchanged. The study remains **STOP_WORKER_TIMEOUT**;
this review does not upgrade its scientific status.

## Independent delivery checks (2026-09-28)

- Reassembled the eight committed parts using the bounded data-only unpacker;
  archive SHA-256 `f22c45a04a380a7fc067ad933b4139ea30ece87771a8d54a9dde7b0c24f9310e`,
  272 members, 62,668 compressed bytes. Every part length/hash and archive hash
  matched `CAPSULE.json`.
- In isolated Docker, `python -S -B -m unittest -v test_candidate`: **8/8 PASS**.
- In the same container, the unchanged `audit.py formal` exited **1 as expected**;
  its output was byte-identical to frozen `AUDIT.json`, preserving the two missing
  denominator errors (missing formal batch-2 manifest and control receipt).
- `prefix_review.py formal` exited **0 as expected** and its output was byte-identical
  to `PREFIX_REVIEW.json`; this is a completed-prefix reconstruction only, with
  `full_scientific_acceptance=false`.
- No allocation, worker, control, corruption campaign, or experiment was rerun.
  No post-freeze tuning or result pooling was performed.

## H / T / D / C / U

- **H:** one sealed immutable snapshot and one stateful sequential reader can
  reproduce the prior pagination bytes while reducing repeated logical reads/hash
  work. The 2048/page-32 CPU gate is still unmeasured.
- **T:** original experiment used Linux x86_64 / CPython 3.13.5. Recovery checks
  used the locally cached `python:3.13.5-slim-bookworm` image, network disabled,
  on an ARM64 Docker host (emulated amd64); this is audit/unit-test replay, not a
  reproduction of the original performance environment.
- **D:** STOP/HOLD retained: only 24/36 workers serialized, zero of 12 formal
  controls completed, and the first 2048/page-1 baseline worker was killed at its
  frozen 8-second limit. No 2048 performance verdict or complete correctness PASS.
- **C:** results apply only to the completed synthetic prefix and the stated
  single-owner sealed-memfd assumptions; descriptive timings are not production
  speedup evidence.
- **U:** 2048 behavior, formal controls, native x86_64 replay, first-page guarantees,
  producer/host integration, concurrency, restart/recovery, model/GUI/task effect,
  physical I/O, and production transfer remain unmeasured.

The source branch had no PR and no branch protection at review time. The recovery
uses its own additive directory and branch; the source remains available until
the PR is merged and all original blobs are verified on `main`.
