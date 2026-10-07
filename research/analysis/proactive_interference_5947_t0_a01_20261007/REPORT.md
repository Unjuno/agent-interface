# Issue #5947 / successor #8313 — matched-context integrity T0 A01

**Status: `PASS_FIXTURE_METHOD_SCOPED`.** This is a deterministic synthetic fixture/provenance result only. It does not test whether a model experiences proactive interference.

## H / T / D / C / U

The allocation and SHA-bound protocol are in [`FREEZE.json`](FREEZE.json). The T0 hypothesis is that four authored arms can vary prior-history representation while holding task/query, final/current state, authority, current-cue byte offset, and exact serialized UTF-8 length fixed within each matched condition×depth stratum. The 32 rows span two query types × depths 0/1/4/8 × four arms: current-only, full conflicting history, equal-volume nonconflicting history, and source-linked supersession ledger. History-required rows retain the observed baseline and ask for the baseline-to-current value pair. The ledger is context only and has no execution authority.

- Candidate ran once in the pinned Python 3.14 Alpine linux/arm64 container; exit 0. Raw: 52,039 bytes, SHA-256 `e3edb93ea783e64f68174a0e9f4c6975001a5c6335db36a39d4bc4da6a190106`.
- Separate raw-only auditor ran once with read-only source/raw mounts; exit 0. It reconstructed 32/32 rows with zero errors and rejected all four frozen mutations.
- Every matched stratum has exact equality of final truth, query, authority, cue offset and UTF-8 bytes; history-required baseline is retained in each arm. The separate position positive control changes cue position.
- Retries: 0. Model, tokenizer, human and GUI calls: 0.

## Interpretation and limitations

The supported claim is that this authored fixture and auditor preserve the declared finite contrasts and reject the listed corruptions. Equal byte counts and cue offset do not imply equal tokenization, visual salience or attention. The expected values and information requirements are authored assumptions; no model-facing serialization was evaluated. No proactive-interference, model accuracy, GUI effect, latency, safety, deployment or generalization claim follows. A later model study remains separately gated and is not authorized by this T0.

The pre-formal construction launcher incident (one test container invocation with the wrong working directory) is recorded in `FREEZE.json`; it did not invoke candidate or formal auditor CLIs. Corrected host and container construction tests both passed 10/10.

## Reproduction

See exact image, source hashes, resource profile, formal commands and output locations in [`FREEZE.json`](FREEZE.json). Raw candidate and audit outputs are retained under `results/`; `RUN_RECORD.json` and `SHA256SUMS.txt` record their identities.
