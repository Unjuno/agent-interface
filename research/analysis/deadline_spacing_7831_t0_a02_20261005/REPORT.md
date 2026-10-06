# Issue #7831 — corrected discrete deadline/spacing T0 A02

Disposition: `PASS_METHOD_SCOPED` for the frozen finite integer-tick model.

## Executed result

The frozen OrbStack run passed all 8 tests. The candidate and separate
exhaustive tick oracle matched all 128 trace/configuration rows and 512
policy rows. Across every one of the 16 latency/uncertainty/spacing
sensitivity combinations, deadline spacing used fewer optional reassessments
than raw triggering on both noisy-oscillation and transient-burst fixtures.
All five hazard/control traces had zero candidate boundary violations;
hard invalidation bypassed pacing with the declared release latency; delayed
and missing due measurements failed closed; every feasible spacing conflict
yielded strictly before the boundary. The endpoint test confirms that an
unreached finite-horizon boundary is `HORIZON_CENSORED`, not a spacing
conflict.

The A02 freeze fixes the discrete endpoint semantics before running:
first nonpositive margin is unsafe, release must occur strictly before that
tick, and the latest safe next sample is the greatest enumerated tick whose
worst-case margin remains positive through response latency. A01's four
oracle mismatches and failed transient discriminator remain unchanged; see
`A01_PREDECESSOR.md` and the original #7831 comments.

## Reproduction

- Exact command: `python -B -m unittest -v test_a02`
- Pinned image: `python:3.12.11-slim@sha256:47ae396f09c1303b8653019811a8498470603d7ffefc29cb07c88f1f8cb3d19f`
- Platform: OrbStack Docker, `linux/arm64`; network disabled, 1 CPU, 1 GiB
  memory, 64 PIDs; actual cgroup readings in `CONTAINER_LIMITS.txt`.
- Result: exit 0, 8/8 tests, 0.005 seconds. Raw output:
  `FORMAL_RAW_OUTPUT.txt`.
- The source tree was mounted read-only. The container run was performed once
  after `FREEZE_A02.json`; no formal retry or post-freeze source edit occurred.
- The pre-freeze host construction gate also passed 8/8. It is not counted as
  the formal result.

## Scope and limitations

This is deterministic synthetic method evidence only. It does not establish
real capture/release latency distributions, GUI event delivery, semantic
hazard detection, task effect, user benefit, safety, or production cadence.
The authored risk trajectories, uncertainty-growth bounds, and response
latencies may omit relevant GUI states or be unavailable in real systems.
The result supports investigating deadline-aware optional reassessment only
where such bounds are independently measured; it does not transfer a
continuous-time event-triggered safety guarantee.

`SHA256SUMS` covers every retained source, freeze, predecessor note, and
result artifact except the checksum file itself.
