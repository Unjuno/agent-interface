# Issue #8135 — T0 persistent-counterparty method assay A02

Fresh successor to A01's `FAIL_INTEGRITY_AUDITOR_EXPECTED_SCHEMA`; A01 remains
immutable and will not be rerun. A02 uses fresh shuffled schedule seed 20261006.
Finite synthetic method test only. No model, browser, GUI, service, account,
credential, live authority, or external effect is used. No predecessor result is
modified. The comparison is inspired by repeated/adaptive interaction, but it
does not claim real services retain or act on agent history.

## H / T / D / C / U

**H.** A persistent history-responsive counterparty changes its later-episode
UI-variant profile conditional on the previous *public* route event, relative
to fresh-reset and frequency-matched history-independent controls. The
simulator will expose that profile while a fixed offline admission oracle
blocks every unauthorized add-on and accepts the authorized positive control.

**T.** Enumerate five arms: `fresh_reset`, `persistent_learner`, `stationary`,
`frequency_sham`, and `persistent_null`; two routes (`plain`,
`effect_boundary`); two seeded public histories (`H_FAST`, `H_CHECKED`); both
route orders; two balanced sham-replication slots; and two episodes per block.
This yields 40 blocks / 80 episode rows. The persistent learner observes only
the seeded public history and its preceding route's public event. The sham's
variant schedule is assigned by replication slot, not by history, route, task
truth, or outcome. Candidate receives no sidecar truth or scorer-only metadata.
UI variants are an authorized positive control and an unauthorized add-on.
Candidate rows contain proposals only; a separate auditor applies the same
frozen hard admission rule and computes synthetic effects.

**D.** `METHOD_PASS_SCOPED` only if the raw-only auditor independently rebuilds
all 80 rows, the full factorial/order/reset/memory schedule and truth outcomes;
detects the planted persistent-vs-reset and persistent-vs-frequency-sham
conditional change; observes the sham's matched marginal frequency without
history dependence; accepts stationary and persistent-null controls; admits
all authorized positives and zero unauthorized effects; and rejects five
mutations (future/private leakage, omission, route-order imbalance, and sham
history dependence). Otherwise `FAIL_METHOD` or `STOP_INTEGRITY`; no H/T1 claim.

**C.** Hand-authored deterministic learners, route-event abstractions and two
variants may make this a test of the protocol implementation rather than
counterparty behavior; exposure rates can match while conditional profiles
differ; an authored truth oracle can be internally consistent but wrong.

**U.** No real UI, persistent service state, human, model, browser cache, task
effect, latency, production adversary, prevalence, safety, or deployment claim.
T0 does not qualify T1 or provide permission to probe a real service.

## One-shot boundary

Construction tests and mount preflight are not candidate/auditor allocations.
After freeze, run one candidate and, only if it exits 0, one raw-only auditor;
retries are zero. Candidate has read-only manifest/source mounts and a distinct
output mount; auditor alone sees sealed truth. OrbStack Docker is offline,
read-only-root, one CPU requested, digest-pinned; requested memory is not
asserted as enforced. Hosted CI tests retained evidence only and must never
rerun either formal role.
