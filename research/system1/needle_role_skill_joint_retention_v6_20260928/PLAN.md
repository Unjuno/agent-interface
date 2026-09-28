# #5081 v6 construction contract

## H — hypothesis

A fail-closed role network with immutable A and an independently updated B
rank-2 LoRA can retain A while acquiring B, under a fully audited real-time
query/update overlap. The existing quality thresholds and four-arm comparison
from #5081 remain unchanged. This is still an explicit synthetic role bit; it
does not test natural-language role recognition or product behavior.

## T — frozen allocation and current base

- Allocation: `needle-role-skill-joint-retention-20260928-v6`.
- Branch: `research/needle-role-skill-joint-retention-v6-20260928`.
- Additive path: `research/system1/needle_role_skill_joint_retention_v6_20260928/`.
- Branch created from main `708dec9bcd2bfb3ef597acf7bc1c8a02bcb96b01`.
- Excluded construction seed: `9980514`; formal seeds: `9980211, 9980311, 9980411`.
- No formal seed is accessed by this construction contract. The previously
  registered formal allocation and quality gates are not tuned or replaced.
- Zero-fit tests bind every realized Docker argv token and require actual
  feedback arrival, consumption and an optimizer interval to overlap an active
  inference-call interval inside that request, with independent
  trainer/inference worker identities. A long query window with only before/after
  inference calls does not qualify.
- `runner.py` creates one fresh feedback row after a dedicated inference
  worker's first real call begins, snapshots the selected adapter, and records
  each inference call interval while the update worker processes the row.
- `audit.py` independently reconstructs event and argv contracts without
  importing candidate `protocol.py`, then imports only the pinned predecessor
  raw auditor to replay inference snapshots and optimizer trajectories.
- `formal.py` has a lease-gated, single-invocation Docker path with no retry;
  it rejects missing or mismatched owner-comment leases before `docker run`.
- No container invocation until coordinator/resource release is explicit.

## D — decisions

Host construction PASS means only that the Python contract functions accept a
complete intended argv/event fixture and reject the listed mutations. It is
not a Docker, concurrency, optimizer, adaptation-quality, latency, or scientific
result. Formal PASS remains exactly as registered in #5081. A missing event,
invalid provenance, non-overlap, shared worker, or malformed clock is an audit
failure/HOLD, never silently reinterpreted as sequential online training.

## C — controls

The construction suite uses only temporary directories and synthetic event
records. No model, optimizer, container, filesystem publication, or action
authority is invoked. Docker argv is an exact token array rather than a shell
string; `--entrypoint=python` explicitly fixes command interpretation. The
launcher is checked structurally and its no-lease validator is exercised; its
formal execution path is not invoked.

## U — limits

Unit fixtures validate the contract implementation, not real event provenance
or OS process scheduling. The complete runner/auditor have not yet consumed a
construction seed, run an optimizer, or been tested against a generated raw
record. A later formal must retain worker/process receipts,
monotonic query and update intervals, each new feedback identifier, actual
realized argv, raw bytes and an independent auditor result. The shared Docker
resource remains gated.
