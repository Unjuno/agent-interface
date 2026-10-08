# Same-clock capture ordering — ordinary engineering A01

Parent: Issue #57; worker `01a0ff33-df63-7d60-871f-a7ecd2649d07`, FINAL-v5.
Starting main: `92ec265bf94697f85d8cdfecde6e2ddf17a53a88`.
Source identities, exact fixture/deck/runner/oracle/auditor hashes and decision
counts are fixed in FREEZE.json before the comparison starts. This is a new
ordinary deterministic regression comparison, not a formal/live allocation or
a replay of #6863, #6870, #6885, #6900 or historical GUI/model experiments.

- **H:** Within the documented shared monotonic clock domain, the current graph
  permits newer sequences/digests with causally impossible capture times to
  authorize progress. A direct capture-order comparison stops those cases while
  retaining completed inputs and their unverified pending effects.
- **T:** The existing two-action fixture, three capture sites and eleven values
  per site, 33 rows per exact baseline/candidate source. One explicit runner
  invocation, followed by one independent raw-only oracle invocation. No threads,
  OS input, model, display, container, shared runtime or formal allocation.
- **D:** Exact coverage; baseline 10 ordering mismatches/24 graph successes,
  candidate zero/14; zero evidence errors; all eight directed raw corruptions
  rejected. Otherwise retain the first failure. No thresholds/rows are dropped
  or changed after observing the result. Ordinary debugging is separately labeled.
- **C:** Sequence freshness is distinct from capture ordering. A trusted adapter
  might already enforce both; the graph must not turn an adapter timestamp
  inconsistency into success. A later clock read is a conservative execution
  boundary, and equal timestamps are allowed. Initial captures need not postdate
  method start; admission retains responsibility for age and target freshness.
- **U:** Timestamps and predicates are authored. No real-clock authentication,
  physical neutral release, independent task effect, live safety, model-call
  saving, latency or cross-domain generalization is established. Existing malformed
  type/sign captures retain their ValueError boundary; exception prefix persistence
  is outside this repair. The oracle checks the declared output/trace fields and
  eight mutations, not arbitrary log authenticity or exact exception text.

The retained five-method RED reproduced ten failures before production changes;
the same methods pass after the minimal ordering guard. The driver clocks are
nanoseconds in a stipulated domain: 10/100/200 at observation return and 20/110
at execution return. They are test inputs, not elapsed-time performance samples.
No mathematical latency or physical control result is inferred from them.

Reproduce the input-free comparison only in a new output directory if explicitly
needed; run_matrix.py uses exclusive raw creation and does not overwrite a first
result. For read-only revalidation, use `python audit.py` in this directory.
