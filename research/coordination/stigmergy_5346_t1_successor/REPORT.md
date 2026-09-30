# Issue #5346 T1 — invalid harness result retained

**Disposition: `STOP_HARNESS_INVALID`.** The single formal run completed, but
post-run source review found its owner-crash lease timing contradicted the
preregistered TTL. The observed simulator/auditor PASS is therefore not a
scientific result for the Issue hypothesis. Do not interpret the aggregate
comparisons as evidence for or against stigmergic coordination.

## Provenance and outcome

- Issue: [#5346](https://github.com/Unjuno/agent-interface/issues/5346).
- Frozen H/T/D/C/U: [`FREEZE.md`](FREEZE.md); preregistration posted in Issue
  comment `5908162967` before the run.
- Runner: [`simulate.py`](simulate.py), SHA-256
  `53476c0e57db53c12dde140b07ba13b798f35f6c6b11b83177389bc0ad349c7a`.
- Independent auditor: [`audit.py`](audit.py), SHA-256
  `11028856ecbc9d0edd241fa90bb83aac3f53bff8f51fc95401551cff582c54ec`.
- Frozen preregistration SHA-256:
  `9396007aa3834836359004f6a9f76f2d5c7499c317740a691ef428a98efa8e70`.
- Raw: [`raw/raw.jsonl`](raw/raw.jsonl), 2,880 rows / 3,467,726 bytes,
  SHA-256 `22bdd03a9c305085071f648a42edb59c5d9104e02cdab60e6f4243afa850b41d`.
- First auditor stdout, retained without rerun: [`AUDIT_FIRST.json`](AUDIT_FIRST.json).
- Container: ID `5d65791a952e6c0468945454aa75ad16946343d2774c0b83f4adb2f990ee2c65`;
  image `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`;
  Docker Engine 29.4.0 linux/aarch64; network `none`; read-only root; 1 CPU;
  256 MiB; 64 PIDs. Exit 0, start `2026-09-30T09:28:54.468986749Z`, finish
  `2026-09-30T09:28:54.921593909Z`.
- Exact formal command (one invocation; no retry):

  ```bash
  docker run --name ai-5346-t1-formal-20260930 --pull=never --network none --read-only --cpus=1 --memory=256m --pids-limit=64 --user 0:0 --tmpfs /tmp:rw,nosuid,nodev,size=64m -v /private/tmp/agent-interface-5315-research-20260930/research/coordination/stigmergy_5346_t1_successor:/src:ro -v /private/tmp/agent-interface-5315-research-20260930/research/coordination/stigmergy_5346_t1_successor/raw:/out:rw --workdir /src python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f python /src/simulate.py --out /out/raw.jsonl
  ```
- The first outcome and disposition were recorded in Issue comment `5908348422`.

## First-auditor output (not a valid scientific pass)

The separate raw-only auditor returned `PASS`, 960 schedules, 2,880 rows, and
zero internal trace errors. Its raw-derived totals were:

| Policy | Blocked admissions | Explicit messages | Completed tasks | Reported unsafe |
|---|---:|---:|---:|---:|
| NONE | 1,320 | 0 | 960 | 0 |
| CENTRAL_CLAIMS | 320 | 2,580 | 960 | 0 |
| LOCAL_MARKERS | 1,064 | 0 | 960 | 0 |

The calculated gates were PASS: local markers reduced blocked attempts at delay
1, while using no explicit messages versus 2,580 central messages. These values
are preserved as what the flawed source did; they are **not** Issue evidence.

## Why the allocation is invalid

The freeze specifies a crashed owner's lease expires after TTL 3. In the runner,
the generic initial-admission branch assigned `release_tick = tick +
TASK_DURATION` (2) even for a crashed owner. For example, raw rows show a crash
at tick 1, but lease release and successor admission at tick 2. Under the frozen
contract that lease must remain until tick 3. This changes recovery timing and
the opportunity for other workers to observe or act on the marker.

The first auditor reconstructed internal acquisition/release consistency but
did not assert the release timestamp against the frozen TTL. Its PASS is thus
an audit miss for preregistration compliance. The source and its first audit
remain unchanged; this report is an additive post-run validity finding.

## Required boundary and next step

- T1 is `STOP_HARNESS_INVALID`, not a scientific FAIL or PASS.
- The T1 allocation will not be rerun. Preserve its exact source, raw, first
  audit output, and this review.
- A distinct successor is justified only with corrected crash-TTL semantics and
  a new independent-auditor check binding release times to the freeze. Any such
  allocation requires its own pre-run registration, seed/schedule identity, and
  one-shot invocation.
- No production/GUI authority, external-effect proof, strategic-agent behavior,
  wall-clock speed, model-token benefit, or roadmap completion is established.
