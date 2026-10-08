# Issue #5385 T1 — adversarial finite alternating refinement

## Question and relation to prior evidence

T0 at `research/analysis/active_automata_learning_5385_t0_v1/` reported exact
agreement for all 2,801 words over seven symbols through depth four. It did not
test whether a safety-relevant divergence just beyond that finite horizon could
be found by a finite input-universal refinement check. This successor preserves
the same seven-symbol alphabet and depth-four comparator; it does not edit,
replace, or reinterpret T0's retained result.

## H / T / D / C / U

- **H:** A five-trace hand suite and exhaustive depth-four trace agreement can
  accept implementations whose stale-retry behavior diverges at depth five,
  while exact reachability over the finite input/output product returns the
  shortest unsafe-output or missing-refusal context and accepts the safe
  implementation.
- **T:** Compare a contract, one safe implementation, and two deliberately
  mutated finite implementations over the same seven inputs. The first mutant
  emits `GRANTED` after `invalidate,retry,retry,retry,effect`; the second omits
  the explicit `RETRY_DENIED` output after
  `invalidate,retry,retry,retry,retry`. Record the five fixed baseline traces,
  every one of the 2,801 words of length 0–4 for each implementation, and a
  breadth-first all-input product exploration until mismatch or state-pair
  closure. A separate raw-only auditor reimplements the contract and product
  check without importing the candidate.
- **D:** PASS only if all three implementations match the hand suite and all
  2,801 depth-four words; the safe implementation refines; both mutants are
  rejected with the shortest expected length-five witness and correct violation
  kind; the independent auditor reproduces every trace/witness; and all four
  corruption controls are rejected. FAIL if a mutant is accepted, the safe
  model is rejected, any bounded word is missing/mismatched, or a violation
  lacks a replayable witness. STOP on source/main drift, unassigned or
  overlapping Docker use, image/platform mismatch, failed gate, or incomplete
  raw/audit retention. No retries.
- **C:** This small finite product may make exhaustive refinement cheap enough
  that active exploration is unnecessary for this case; alternatively, the
  chosen interface semantics may over-penalize safe refusal.
- **U:** The alphabet and deterministic finite machines are authored fixtures.
  Product-state closure is exact only for these machines and this input/output
  relation; no nondeterminism, hidden GUI effect, noisy observation, runtime
  authority, live API, user data, learned policy, production safety, or product
  benefit is tested. `REFINES` here means every finite product pair/input was
  explored under the explicitly defined input-universal/output-subset rule; it
  is not a general certificate for real interfaces.

## Frozen design

- Input alphabet: the seven Issue #5385 T0 symbols, in the same order.
- Baseline: five fixed traces, followed by exhaustive depth 0–4 coverage
  (`1 + 7 + 49 + 343 + 2401 = 2801` words).
- Candidate cases: `safe`, `unsafe_output`, `missing_refusal`.
- Refinement relation: every contract/environment input is explored at every
  reachable product pair; an implementation must produce a non-empty explicit
  output set, and every emitted output must be included in the contract's
  permitted output set. Mismatch search is breadth-first, so the returned word
  is shortest within the finite deterministic product.
- Formal invocation budget: one candidate CLI invocation; one independent audit
  CLI invocation only if the candidate exits zero; zero retries.
- Expected concrete witnesses (not treated as results until execution):
  - `unsafe_output`: `invalidate,retry,retry,retry,effect`,
    `OUTPUT_OUTSIDE_GUARANTEE`.
  - `missing_refusal`: `invalidate,retry,retry,retry,retry`,
    `MISSING_EXPLICIT_REFUSAL`.
- Construction verification: stdlib-only Python unit tests. Formal candidate
  and auditor: separate Docker Desktop containers, pinned cached
  `python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`,
  `linux/amd64`, network disabled, read-only source/root, separate writable
  output, one CPU, 256 MiB, 64 pids, all capabilities dropped, and
  no-new-privileges. No pull/build, model, GPU, GUI, X11, external effect, or
  user data.

## Exact formal commands

Run from a fresh Docker launch gate only after a unique exact CPU-only slot is
reconciled in #5085. Replace `<source>` and `<output>` with verified absolute
paths, and `<freeze-commit>` with the immutable source commit. Do not use
`--pull`; any changed main, slot, context, cached digest, or platform is STOP.

```powershell
docker run --rm --network none --cpus=1 --memory=256m --pids-limit=64 `
  --read-only --tmpfs /tmp:rw,noexec,nosuid,size=16m `
  --security-opt no-new-privileges --cap-drop ALL `
  -v "<source>:/src:ro" -v "<output>:/out:rw" -w /src `
  python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9 `
  python experiment.py --output /out/formal.jsonl --source-commit <freeze-commit> `
  --allocation-id active-automata-5385-t1-docker-desktop-20261001-01
```

```powershell
docker run --rm --network none --cpus=1 --memory=256m --pids-limit=64 `
  --read-only --tmpfs /tmp:rw,noexec,nosuid,size=16m `
  --security-opt no-new-privileges --cap-drop ALL `
  -v "<source>:/src:ro" -v "<output>:/out:rw" -w /src `
  python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9 `
  python audit.py --raw /out/formal.jsonl --output /out/audit.json
```

The candidate is invoked only once. Run the auditor once only after candidate
exit 0; if either formal command or its result gate fails, preserve it and do
not retry under this allocation.
