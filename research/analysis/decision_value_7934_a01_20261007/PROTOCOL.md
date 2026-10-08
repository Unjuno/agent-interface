# Frozen execution protocol

Allocation: `7934-DECISION-VALUE-ACQUISITION-A01-20261007`.

## Inputs and separation

- `fixtures/candidate_model.json` contains the stipulated supported-state
  model, safe routes, check-signal mapping, prior history, and arm thresholds.
- `fixtures/scoring_key.json` is scorer-only and names realized worlds. The
  candidate never reads this file; it receives no `true_state` field.
- `candidate.py` computes check metrics and route maps from the public model.
- `scorer.py` joins candidate decisions to scoring-only worlds and computes
  realized regret, query cost, yield and hard-gate outcomes.
- `auditor.py` separately reimplements the posterior, entropy, expected-risk,
  selection, route, score and mutation checks. It imports neither candidate nor
  scorer.

The input is a static exact finite model, not a stochastic GUI simulator.
“Held out” denotes the eight-state topology fixed as a confirmatory case before
formal execution; no parameter is fit from either topology.

## Formal execution (one call each; in order)

From this directory:

1. `python3 -B candidate.py fixtures/candidate_model.json results/formal01/candidate.raw.json`
2. `python3 -B scorer.py fixtures/candidate_model.json fixtures/scoring_key.json results/formal01/candidate.raw.json results/formal01/score.json`
3. `python3 -B auditor.py fixtures/candidate_model.json fixtures/scoring_key.json results/formal01/candidate.raw.json results/formal01/score.json results/formal01/audit.json`

Record the exact command, interpreter/host, start/end, exit code and SHA-256
for every source, input and output. Candidate, scorer and auditor each run once
for this frozen formal allocation. Construction unit tests are excluded from
these counts. Any formal exit/input/hash/audit failure is retained as the
terminal allocation outcome; do not rerun.

## Runtime and isolation boundary

Read-only OrbStack preflight found a reachable Docker 29.4.0 linux/arm64 daemon,
but `python:3.12-slim` image inspection failed on a containerd content blob with
`operation not supported`; image listing also failed on a different blob.
There were no running containers at preflight. No pull, build, restart, prune,
repair, or unrelated container modification is authorized or attempted.

This CPU-only pure-stdlib T0 has no GUI, model, network, live resource
allocation, or external effect requirement. Therefore use the declared native
macOS/Python fallback once and make **no container/isolation claim**. Preserve
the engine failures as infrastructure evidence. If the frozen native runtime
cannot be recorded or the exact main/source identities differ immediately
before formal execution, STOP with candidate/scorer/auditor counts 0/0/0.
