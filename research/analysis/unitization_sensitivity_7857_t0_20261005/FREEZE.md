## Prospective T0 freeze — UNITIZATION-7857-T0-A01 (2026-10-05)

No direct open PR or branch owner was found for #7857 during the intake check. This is the bounded CPU-only synthetic T0 from this Issue, not T1 eligibility and not a live trace allocation.

### H / T / D / C / U

**H:** For some plausible segmentations of a synthetic continuous-trace family, exact unit boundaries materially change singleton/doubleton occupancy or the held-out new-mode episode-unit rate. A preregistered sensitivity gate detects these cases even where category agreement on forced-aligned units is high. An explicitly unambiguous control remains stable and unflagged. A null remains possible if downstream statistics are invariant.

**T:** Seven fixed traces: training S1 has (1) two same-mode A episodes separated by a 2-unit quiet gap, (2) one C episode with missing telemetry from [34,37), and (3) an unambiguous D control. Training S2 has (4) overlapping B/C cascade symptoms, (5) right-censored E ending at observed time 50 with its partial episode retained, and (6) stable A. The held-out trace contains two same-mode novel F episodes separated by a 3-unit gap plus known A. Two frozen synthetic segmenter outputs A/B are compared. Compute exact-span match F1 (custom exact-boundary diagnostic; not Krippendorff's alpha), per-trace matches, conditional category agreement on six declared aligned units, per-stratum training mode counts/singletons/doubletons, held-out new-mode episode-unit rate, and the frozen saturation decision (singleton fraction ≤0.15 and new-mode rate ≤0.5). Do not treat this finite sensitivity interval as a population confidence interval.

**D:** PASS_METHOD_SCOPED only if the independent oracle reconstructs all seven trace denominators and both annotation sets; unit-boundary metrics and category agreement are reported separately; S1 occupancy and held-out new-mode rate are identified as segmentation-sensitive; the exact unambiguous control is not flagged; saturation results are reported without promotion; and all five raw-input mutations are detected: forced consensus, merge count error, split control into independent trials, omit censored trace, and post-outcome boundary tuning. Any mismatch is FAIL_METHOD. Image/source/mount failure before candidate is STOP_ENVIRONMENT with no retry.

**C:** These annotations are synthetic deterministic segmenter outputs, not independent human adjudications. An exact-span F1 may over-penalize near-boundaries and is not unitizing alpha. Occupancy and held-out estimates are descriptive for this authored fixture; alternative event-key rules or mechanism taxonomy may dominate the result.

**U:** No natural trace-family reliability, population discovery yield, causal truth, failure rate, safety, catastrophic-mode coverage, runtime behavior, or user/task effect follows. No model, GUI, user data, action authority, network, or GPU is used.

### Frozen identity

Freeze base main: 3bf3d49bec2aa26a9aaba38806f9e88296459356.
Fixture Git blob dee36b671a004bfe23a10ee09b891f7285f68329; SHA-256 a43607c04fb526a71470971688f7c54f9f9a19ad0e8f5ee82a41b2ab1f1f9b80.
Candidate Git blob b6bdf89f9c1a3cf87fd10fe146183c2827d524f2; SHA-256 873a4a74afffed62c398d58c5d514fb5b68d21d2819716d5e722ee7bd11d4e4f.
Independent auditor Git blob aa0c42767f7fa0a603ededcc6540847def7b9a51; SHA-256 0b253b2f4281d2683cf8ce9baf1bf4e6ffe11def3d9ab7d6d96101f2dd892d24.
Pre-freeze construction probes: C01 candidate omitted the occupancy field and independent audit failed (preserved); C02 fixed that output field and independently passed 5/5 mutation checks. Sources and both outcomes are retained in Git blobs: edda909ebaa8c4b187b48226630dd84929f86161, 604bb0a07f669cdb63e445db238fdac6cdde4f68, 7bde93c51201cb9e31f8501b141df46d383ecb15, 18372767d50febb441b97aceb56d5f1f1e1e49ff, 30da962e9fa5d3d6e4cf370e54cc120d855d5c07, and 1288f1fbf2951cd6ee05a92e677c58e259ae7752. They are construction evidence, not formal attempts.

Runtime: WSLc 3.0.1.0; linux/amd64 node@sha256:0a7108bf6c7bf5de370ffb1a3ed6be93d405b43ff159f681a8d18c0e2bc2e402 (Node v22.23.3), cached, pull never, network none, CPU 1, --rm, read-only source/input and separate writable outputs. Formal candidate/auditor limits 1/1; invocations 0/0 at freeze, retries 0.

Candidate:
wslc.exe run --rm --pull never --network none --cpus 1 --volume "C:\Users\junny\Documents\Codex\2026-09-19\new-chat\_tmp\unitization-7857-t0-20261005\src:/src:ro" --volume "C:\Users\junny\Documents\Codex\2026-09-19\new-chat\_tmp\unitization-7857-t0-20261005\candidate-out:/out" --workdir /src node@sha256:0a7108bf6c7bf5de370ffb1a3ed6be93d405b43ff159f681a8d18c0e2bc2e402 sh -lc "node candidate.js > /out/candidate.json"

Auditor:
wslc.exe run --rm --pull never --network none --cpus 1 --volume "C:\Users\junny\Documents\Codex\2026-09-19\new-chat\_tmp\unitization-7857-t0-20261005\src:/src:ro" --volume "C:\Users\junny\Documents\Codex\2026-09-19\new-chat\_tmp\unitization-7857-t0-20261005\candidate-out:/input:ro" --volume "C:\Users\junny\Documents\Codex\2026-09-19\new-chat\_tmp\unitization-7857-t0-20261005\audit-out:/out" --workdir /src node@sha256:0a7108bf6c7bf5de370ffb1a3ed6be93d405b43ff159f681a8d18c0e2bc2e402 sh -lc "node auditor.js > /out/audit.json"