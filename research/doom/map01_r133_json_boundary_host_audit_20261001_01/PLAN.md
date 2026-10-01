# MAP01 adjudicator JSON boundary — host construction successor

Status: pre-run host-only construction. This is additive to the STOPped formal
T0 and the candidate-only host result on Issue #59; neither predecessor is
rewritten or treated as audited evidence.

## H / T / D / C / U

- **H:** The current-main paired adjudicator rejects JSON type substitutions
  and invalid row count after a canonical JSON wire round-trip. A separate
  raw-only auditor can verify the actual wire payloads, exact rejection
  reasons, and source identity without importing candidate adjudication code.
- **T:** Pin current main, the upstream v2 adjudicator, this plan, candidate,
  auditor and construction tests. Run tests before freeze. Then execute the
  host candidate exactly once: one valid six-row fixture plus eight malformed
  controls (boolean `pair_id`, boolean `session_order`, float `ready_ns`, int
  `map_exit`, boolean `kill_count_gain`, float `audit_error_count`, non-string
  `fixture_sha256`, and five-row cardinality). Store exact canonical wire JSON,
  parsed rows, candidate disposition/reason, hashes and invocation receipt.
  Only if candidate exits 0, execute a separate raw-only auditor exactly once.
  The auditor independently checks all cases and four copied-evidence
  mutations: omission, duplicate, forged decision, altered bound identity.
- **D:** `PASS_HOST_JSON_BOUNDARY_AUDITED` iff the source/freeze/raw hashes
  match; pristine valid case returns instrumentation pass; all eight malformed
  cases return the exact preregistered `STOP_INTEGRITY` reasons; the independent
  auditor reports zero errors; and all four copied-evidence mutations reject.
  Any accepted malformed case is `FAIL_HOST_JSON_BOUNDARY`; provenance or
  audit mismatch is `STOP_HOST_AUDIT`. This does not satisfy the separately
  gated container formal allocation.
- **C:** CPython 3 standard library on the host; deterministic synthetic rows;
  no Docker/OrbStack, game, X11, GUI, model, GPU, network call, input, or
  external effect. The candidate reads only the frozen repository adjudicator.
- **U:** No evidence about threat exposure, real MAP01 behavior, safety under
  live execution, comparative recovery efficacy, transport-layer JSON
  behavior, or runtime promotion. `UNCERTAIN` on the synthetic positive fixture
  is not a MAP01 outcome.

The prior exact formal allocation remains `STOP_RESOURCE_COORDINATION` and is
not reused. This successor is a different host-only construction rung designed
to make the candidate-only host observation reproducible and independently
auditable; it does not authorize any shared container operation.
