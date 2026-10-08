# Issue #8500 — T0 A01 formal result

**Disposition: `PASS_METHOD_SCOPED`.** The fixed deterministic scorer produced 84 rows across 12 blocks. The independent auditor exited 0, reconstructed the registered outputs with no errors, and rejected all five frozen corruption controls. The candidate and auditor each ran once; retries: zero. Raw outputs are [`candidate.json`](candidate.json) and [`AUDIT.json`](AUDIT.json); exact commands, environment, timestamps, exit codes, and hashes are in [`RUN.json`](RUN.json).

## Result within the frozen synthetic fixture

For 14 authored invalid candidates across the eight base targets, invalid proposals were 8/14 (57.1%) with no memory, 5/14 (35.7%) with prose rejection notes, and 2/14 (14.3%) with structured counterexamples plus a fresh boundary check. Base valid-candidate recall was 8/10 (80%) in every arm. In the four changed-envelope controls, structured memory reopened and freshly checked all four candidates; combined valid recall was 12/14 (85.7%) for no-memory and structured, and 11/14 (78.6%) for prose.

These are descriptive counts for a hand-authored finite fixture and a fixed rule scorer. They do **not** establish real analogical reasoning, model behavior, generalization, literature-derived novelty, deployed-memory effectiveness, or Agent Interface product benefit. The oracle and counterexamples were authored for this test; whitespace word units are not model tokens.

## Reproduction and provenance

The preregistered package was committed before execution at `db28a7feeed1426e81cd08b2f84cbfbc100ae696` on `research/analogy-rejection-8500-t0-a01-20261008`. All 11 published file blobs were read back and matched their Git object IDs before either formal command ran. Formal execution used the supplied Windows host, CPython 3.12.10, standard library only; this finite test did not require a container boundary and is not a Docker/WSLc comparison.

Construction history and failures are retained in [`CONSTRUCTION.md`](CONSTRUCTION.md). The frozen protocol and source files were not changed after formal execution began; this result and raw outputs are additive.
