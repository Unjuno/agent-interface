# Needle intent-capacity replication — Issue #4778

Allocation `needle-intent-capacity-4679-v2`; branch
`research/needle-intent-capacity-4679-v2-20260927`; additive path
`research/system1/needle_intent_capacity_4679_v2/`.

## H — hypothesis

On fresh seeds, the 10→64→64→4 intent-conditioned Needle delegate will meet
every frozen held-out fidelity/safety gate under the same synthetic teacher
and training recipe; the 10→24→24→4 reference will miss at least one core
fidelity gate in at least two seeds, while the state-only 6→24→24→4 negative
control remains weak. This is a fresh-seed replication of #4679's scoped
capacity finding, not evidence of real-world skill transfer.

## T — frozen treatment

Fresh base seeds: 4153201, 4153203, 4153207. Train-state seed = base;
held-out-state seed = base+1; state-only initialization = base+10; both
intent-aware widths = base+20. Each split contains 4096 train and 2048 disjoint
held-out base states, expanded over the exact four #4153 intents and labels.
The generator, teacher, data sizes, full-batch cross-entropy AdamW recipe
(lr 0.006, weight decay 1e-4), and 900 updates/fit remain fixed. Arms:
STATE_ONLY_24, INTENT_AWARE_24, INTENT_AWARE_64. Exactly nine fits; one
trainer invocation plus a separate independent raw-only audit. No retries,
tuning, seed replacement, model pull/install, or post-result extension.

Before freeze, repeat all 15 base/derived seed collision searches across
open/closed Issues, PRs, branches, commits and main code. Freeze exact main,
branch, source SHA-256/Git blob SHA pairs, issue-body SHA-256, and cached Docker
image ID/platform; read all source bytes back from the allocated branch before
any optimizer step. Inspect the local image tag before and after the formal
run. The current image ID at intake is
`sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e`;
STOP if the value differs. The formal wrapper uses the tag
`needle-pilot05:local`, not a digest as a tag.

Container limits: Docker 29.8.0, Linux/amd64 CPU, one CPU and one Torch thread,
2 GiB, 64 PIDs, network none, read-only source/root, bounded tmpfs,
`--pull=never`, `--security-opt=no-new-privileges`. All outputs are synthetic,
authority false and zero action emissions.

Construction-only tests run before freeze and perform zero optimizer steps.
The host formal wrapper is separately frozen and requires the exact GitHub
readback freeze before creating its one-use marker. It captures complete argv,
wall timestamps, exit codes, stdout/stderr, all raw cells, auditor output and
SHA-256 manifest. Trainer and auditor execute in separate containers.

## D — decisions

Each width-64 seed must meet all frozen gates: accuracy ≥0.97;
exact-all-intents ≥0.90; disagreeing-intent accuracy ≥0.96; OUT_OF_SCOPE YIELD
recall ≥0.995; action-on-teacher-YIELD ≤0.01; forbidden-effect proposal rate
≤0.01. Require teacher-disagree base fraction ≥0.50, STATE_ONLY_24
exact-all-intents ≤0.60, every invalid-intent control YIELD, exact prediction
recomputation from saved tensors, and independent audit with zero errors.
The state-only accuracy gate is the negative-control discriminator; a raw
label-disagreement fraction is descriptive only because different intents can
legitimately receive different teacher labels even without intent input.

- `PASS_CAPACITY_CLOSED_GAP_SCOPED`: width 64 passes every gate in all seeds
  and width 24 misses a core accuracy/exact/disagree gate in at least two.
- `PASS_INTENT_FIDELITY_NO_CAPACITY_NEEDED`: both widths pass every seed.
- `FAIL_CAPACITY_NOT_SUFFICIENT`: integrity passes but width 64 fails any gate.
- `INCONCLUSIVE_MIXED_CAPACITY`: any other integrity-valid pattern.
- Source/image/execution/audit provenance defects are typed STOP, not scientific
  FAIL.

## C — alternatives

Width may not be causal; seed variance, optimization dynamics, one-hot
representation limits and synthetic teacher-boundary complexity remain
alternatives. Fit time and model size are descriptive, not post-hoc gates.

## U — limits

Three fresh seeds, one synthetic task family, one host and one CPU image. No
natural-language intent fidelity, Astra demonstration transfer, online
learning, GUI/task success, cross-hardware behavior, action safety, runtime
suitability or product readiness follows.
