# V39 per-key measurement consumer A02

This successor also stopped on an input-hash mismatch. A01 remains preserved;
A02 has its own freeze, run ID and output directory. The digests were copied
manually instead of generated from the pinned input, repeating the same setup
failure.

## Retained input and A02 STOP

The input is byte-identical to Git blob eacb735634d6c6761ba7fa39448e6d7d43e342d5,
whose SHA-256 is recorded in results/a02/STOP.json. The sole A02 invocation
expected a different digest and stopped before producing candidate output.
The consumer, audit and mutation tests did not complete. See DISPOSITION.md.

No candidate or measurement-consumer PASS is claimed. The input is one prior
fake-display pair and provides no live game, effect, useful feedback, threat
response, recovery or MAP01 result.

## H / T / D / C / U

- **H:** Correctly pinned V12 down/up measurement rows can feed a fail-closed
  per-key interval consumer without granting authority/effect.
- **T:** One new A02 replay over immutable A01 input bytes, separate raw-only
  audit, ten negative/mutation controls.
- **D:** PASS only if one confirmed identity-matched pair is bracket-consistent,
  strictly ordered, and exactly reconstructed; the auditor must reject altered
  candidate output.
- **C:** Fake-display instrumentation and a single pair do not measure a live
  game or recovery, and a sample bracket is not exact physical occupancy.
- **U:** One F8 pair; no live allocation or broad claim.

## Reproduction

A02 was frozen as one-shot and its output directory was claimed by the retained
STOP. Do not rerun it. Any continuation needs a separately versioned freeze
and output path; the A01 and A02 failures are preserved unchanged.
