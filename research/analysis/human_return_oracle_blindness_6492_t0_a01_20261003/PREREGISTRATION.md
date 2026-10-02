# Preregistration — #6492 oracle-blind return-cue packets A01

## Lineage and question

Successor to #6492 and its retained T0 evidence in #6499 and #6520. The prior three-arm candidate environment included a synthetic `pending_step_code` field containing oracle return-action labels. That record remains `PASS_METHOD_SCOPED` for emitted-packet/provenance checks, not strict candidate/oracle blindness. The separate modal-baseline result remains distinct and is not pooled. This allocation tests whether a bounded candidate packet remains invariant under observationally identical public views paired with different hidden return labels.

## H / T / D / C / U

**H.** In a finite synthetic return-to-own-work fixture, byte-identical public return-view inputs paired with different hidden correct-return labels produce byte-identical, non-authoritative candidate packets with no guessed target. A fresh user-authored cue may be surfaced as context; stale or agent-authored cues, changed-app and wrong-window cases remain `UNKNOWN`. A packet never grants action authority.

**T0.** Use fourteen frozen public rows: four observational-equivalence pairs (eight rows) with conflicting hidden return labels, plus six controls: a fresh user-authored cue, a stale cue after external app change, an agent-authored cue, a wrong-window view, an offered-but-unused cue, and an emergency-release obligation. `candidate-input/public.json` is the only fixture input mounted into the candidate. `auditor-input/truth.json` and the frozen ordinal map are never mounted into the candidate; they are only provided read-only to the later independent auditor. Candidate emits a bounded packet/status, not a return action. The auditor independently reconstructs expected packets from public evidence, hidden truth and ordinal mapping, without importing candidate code.

The finite outcome is method validity only. No wall-clock or participant effect is measured. Construction tests may invoke candidate/auditor on temporary fixtures on the Mac host; those are explicitly non-formal. Formal sequence is exactly one construction test suite, one candidate-container invocation, then one separate auditor-container invocation; retry budget zero. Formal outputs must be absent before the final freeze. A failed source, base, image, path, isolation or collision gate is a pre-candidate `STOP`, not a scientific failure.

Infrastructure-only OrbStack construction probes (not candidate/auditor code) confirmed that the public fixture mount was read-only, auditor truth was absent, the root filesystem was read-only, and effective cgroup values were `memory.max=536870912` and `cpu.max=100000 100000`. A second probe confirmed UID 65534 can write only through a distinct writable output bind mount. Probe outputs, IDs, and the write sentinel are retained under `construction/`; both containers were auto-removed.

**D.** `PASS_METHOD_SCOPED` only if all four conflicting-truth pairs have byte-identical public rows and candidate packets, with no target-specific claim; the fresh user cue is surfaced only as user-provided context; stale, agent-authored, wrong-window and unused-offer controls remain `UNKNOWN`; the emergency release obligation is retained; the raw-only auditor reconstructs 14/14 rows with zero errors; and all eight frozen mutations are rejected. A guessed target, hidden-truth access, stale-cue promotion, lost release, or audit discrepancy is `FAIL_METHOD`.

**C.** The fixture is authored and the candidate is deterministic. Uniform abstention can satisfy the non-guessing side; this test does not demonstrate useful human resumption or agency benefit. Hidden-label mapping is finite and does not simulate a natural desktop session.

**U.** No participants, audio, GUI, private data, model, live task, real effect, human memory, latency, accessibility, privacy, safety, or product claim. No T1 authority follows.

## Frozen runtime and execution boundary

- Host/runtime: macOS arm64; dedicated isolated OrbStack Linux VM and private Docker Engine for this allocation. A read-only host-engine name/status and image-metadata inventory was performed before allocation to discover the active shared container; no container-internal inspect, exec, lifecycle operation or mutation occurred. This intake disclosure is retained in Issue #6819. Formal candidate/auditor runs use only the private VM Engine; the shared OrbStack Engine and its existing containers are not used or modified.
- Candidate and auditor use separate containers from cached `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f` (`linux/arm64`). Formal `docker run` uses `--pull=never --network=none --cpus=1 --memory=512m --user 65534:65534 --read-only --cap-drop=ALL --security-opt=no-new-privileges`.
- Source and candidate/public inputs are read-only in the candidate; candidate output is in a distinct writable mount. The auditor receives its own source, public fixture, hidden truth and candidate raw output read-only, plus a distinct audit output mount. It does not receive candidate source.
- VM/engine/image setup and digest verification occur before the formal source freeze. Network is not available inside either experiment container. No model, GUI, external action or GPU is involved.

## Additive locations

- Branch: `research/6492-oracle-blind-cues-t0-a01-orbstack-20261003`
- Package: `research/analysis/human_return_oracle_blindness_6492_t0_a01_20261003/`
- Allocation: `HUMAN-RETURN-6492-ORACLE-BLINDNESS-A01-20261003-01`
- Base main: recorded in `FREEZE.json` immediately before formal candidate execution.

No formal candidate or auditor output is claimed in this preregistration.
