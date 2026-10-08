# Issue #6500 — origin-to-effect binding T0

## Disposition

**`PASS_METHOD_SCOPED` for the authored finite metadata table only.** Candidate and independent auditor each ran once in separate pinned OrbStack containers; retries 0. The auditor reconstructed 24/24 unique policy/case rows with zero errors and rejected all six frozen mutation controls.

The `ORIGIN_BOUND` classifier allowed both legitimate fresh cases (2/2), falsely allowed none of the six nonlegitimate cases, and left missing process provenance as `UNKNOWN`. In the same authored table, `VISUAL_ONLY` and `SIMILARITY_ALARM` each falsely allowed six nonlegitimate cases. This is a deterministic method discriminator, not an estimate of real-world error rates.

## Frozen cases and measured classifications

Eight authored cases were crossed with three decision rules: two legitimate fresh controls (including one with a high alarm score), a pixel/label-matched low-alarm lookalike, stale window reuse, post-capture replacement, unknown process provenance, untrusted embedded content, and wrong effect recipient within the nominally trusted app.

| Classifier | False allows among six nonlegitimate rows | Legitimate fresh rows allowed |
|---|---:|---:|
| `VISUAL_ONLY` | 6/6 | 2/2 |
| `SIMILARITY_ALARM` | 6/6 | 1/2 |
| `ORIGIN_BOUND` | 0/6 | 2/2 |

For the origin-bound arm, stale generation and incomplete process provenance returned `UNKNOWN`; known origin/embedded-content/target/recipient conflicts returned `MISMATCH`. These outputs are scoped classifier results only, not authority to act.

Mutation controls: origin swap, stale generation, similarity-score inversion, embedded-origin omission, target identity change, and recipient misbinding; all six were rejected. The full row-level raw, audit, exact argv, logs, and container inspect receipts are retained under `results/formal_01/`.

## Execution identities

- Allocation: `ORIGIN-EFFECT-BINDING-6500-ORB-T0-20261002-01`.
- Source commit: `a7941a435523a8026bb3dbd905cbada9e50891f6`; freeze commit: `772522ac85cad8863948c2d7dd6f44bfcd896810`.
- Freeze JSON SHA-256: `93fd5b4605fa32008a123d9055525c8a4d7973ca9b38b88838e725320b00b979`.
- Candidate container ID: `d96f036221e2ef47e332cbabe17f7ab849faaf3fb49522e93ce2403823a5962f`; exit 0.
- Auditor container ID: `74a994680d815e4bd3e296b7daf1aaf521bc1dabbef3568e02bfbc2ca0cd42ce`; exit 0.
- Candidate raw: SHA-256 `25b1ce94671842e32a4a305492885b49732f2bff8c07504e6c5ec432ba597b0e`.
- Audit JSON: SHA-256 `05cd08ed727def779aa02023f51fc280f1f42dc191a7ef11d49ab98ce3805645`.
- Cached pinned `python:3.12-slim-bookworm` on OrbStack, pull never, network none, read-only root/source, 1 CPU, 256 MiB requested, 64 PIDs. Both exited normally with `OOMKilled=false`. Construction suite 8/8 passed on host and 8/8 in a separate disposable OrbStack container. The initial preformal no-op mutation assertion and its correction are transparently retained in `CONSTRUCTION.md`.

## Limits

No actual app/window/process provenance was queried, no spoof was staged, and no GUI input or effect occurred. The finite table stipulates complete and truthful origin, generation, target, and recipient metadata. This does not establish that any OS API can supply those facts authentically or atomically, that race conditions are prevented, or that origin is equivalent to user authorization. No security, safety, real-world prevalence, runtime, or product claim follows; no T1 is authorized by this result.
