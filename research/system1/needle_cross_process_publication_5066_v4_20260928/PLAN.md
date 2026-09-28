# Issue #5082 — concurrent readers across atomic publication

## Allocation and lineage

- Successor to #5066 post-merge correction; preserve every predecessor source, result, audit, raw file and PR unchanged.
- Allocation: needle-cross-process-publication-overlap-5066-v4-20260928-01.
- Branch: research/needle-publication-5082-audit-v4-20260928.
- Additive path: research/system1/needle_cross_process_publication_5066_v4_20260928/.
- Intake and source-publication main: c2f0eb2dc03d6949942be7f8ccb463f41975393e.
- Formal execution at this freeze stage: 0; no Docker runner/auditor invocation.

## H / T / D / C / U

**H.** During 4,096 same-directory atomic os.replace publications on a dedicated container-local Linux tmpfs, four independent readers opening one package path concurrently observe only complete, digest-valid packages from the frozen generation set. A barrier-controlled truncate/partial-write diagnostic exposes invalid partial bytes.

**T.** Reuse the exact inert seed-3788 package bytes by Git blob and SHA-256, copied into this additive directory as base64 data. Use one publisher and four fresh reader processes per arm. Each reader takes an initial old-package sample, acknowledges readiness, then loops through bounded open/read/hash/parse observations until the writer stops. Record every row in a distinct JSONL file. Atomic arm uses exactly 4,096 candidate generations, same-directory temporary files and os.replace; record monotonic call brackets. Diagnostic arm sets a phase marker before truncation, writes exactly half of a candidate, and waits until every independent reader has observed invalid partial bytes before completing the write. The auditor receives the raw evidence bind read-only at `/raw` and writes only to a distinct `/audit` bind; formal stdout, stderr, and invocation receipt stay in a host-side `formal/` directory outside both mounts.

**D.** Scoped PASS requires all 4,096 replacements, all four reader identities/exits/logs per arm, no observation cap, all atomic complete reads byte-identical to a regenerated whole package, at least 32 open-call intervals overlapping replace-call intervals across at least two reader PIDs, at least one exact invalid partial diagnostic read, 16/16 frozen corruption controls rejected, a read-only raw input mount for the auditor, and zero independent audit errors. The auditor additionally binds each publication interval inside the writer envelope, requires each reader exit timestamp to follow its final read, and limits complete diagnostic generations by phase (phase 0: seed only; phase 1: seed/final only in addition to the exact partial prefix; phase 2: final only). Zero qualifying overlaps is HOLD, not proof of atomicity. Accepted malformed bytes are FAIL. Missing provenance/process evidence is HOLD. One formal orchestration, no retry or post-result tuning.

**C.** One Docker Desktop Linux/amd64 container filesystem, one host monotonic clock and finite synthetic JSON package. Bracket overlap is wall-clock call-interval evidence, not a kernel-internal linearization timestamp or race-rate estimate. No fsync is used in the atomic arm.

**U.** No crash/power-loss durability, network filesystem, cross-host semantics, model/LoRA, GUI/task effect, dispatch authority, production safety, latency or product claim.

## Frozen environment and integrity

- Image: sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9, linux/amd64; Docker Desktop desktop-linux. Every inspect/info/ps/run call explicitly pins `--context desktop-linux`. `/scratch` is a dedicated 32 MiB tmpfs for the active package and rename candidates; runner raw output is a dedicated `/out` bind. The separate auditor sees that bind only as read-only `/raw` and has a different writable `/audit` bind. The runner refuses to start unless `/scratch` is mounted as tmpfs.
- Network disabled, pull never, root/source read-only, CPU 0.5, memory 256 MiB, PIDs 32, shm 32 MiB, all capabilities dropped, no-new-privileges.
- Nested .gitattributes uses * -text, preserving exact committed/check-out bytes across Windows and Linux. The freeze binds both SHA-256 and Git blob identity for every source and the copied input.
- Stage 0 tests are construction-only and excluded. Preflight rejects source/input/image/context mismatch, existing output and any running Docker container before output creation. A fresh exclusive slot is required immediately before the sole formal orchestration.
