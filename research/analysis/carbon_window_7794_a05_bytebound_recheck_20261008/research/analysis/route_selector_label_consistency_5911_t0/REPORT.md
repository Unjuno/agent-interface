# Issue #5911 route-selector label consistency T0

**Result: `PASS_METHOD_SCOPED`** for a synthetic finite fixture and its
independent exhaustive route-set audit. This does not establish a real-trace
causal or optimization result.

## Outcome

At the exact frozen main base `8afb359a4052d0b242337965378b5917338b3267`,
the candidate ran once and the separate auditor ran once. The auditor returned
five rows, `errors=[]`, and `PASS_METHOD_SCOPED`. Candidate raw SHA-256 is
`241cf937ab680c4bbaae40065525b982b7e3280b9f0bf30bfe972ccb93cddc09`.

| Case | Selector | Baseline optimum | Intervention optimum | Disposition | Endpoint delta |
|---|---|---|---|---|---:|
| half_model | min cost | model (130 ms) | model (80 ms) | ROUTE_STABLE | -50 ms |
| plus_80 | min cost | model (130 ms) | model (210 ms) | ROUTE_STABLE | +80 ms |
| route_switch | min cost | model (130 ms) | alternate (260 ms) | NONSTATIONARY_INTERVENTION | withheld |
| exact_tie | min cost | model (130 ms) | alternate + model (260 ms each) | TIE_SET | withheld |
| max_cost_control | max cost | alternate (260 ms) | alternate (260 ms) | ROUTE_STABLE | 0 ms |

Thus the explicitly competing 260 ms endpoint does not become selected after
the +80 ms model intervention (210 < 260); the separately authored 280 ms
case does switch. The exact 260 ms tie remains set-valued rather than
silently choosing one route.

## H / T / D / C / U

- **H:** Branch-change/stationarity is derived from the selected endpoint set
  before and after applying the intervention to the same finite route graph.
- **T:** Five fixed two-endpoint cases, explicit min/max selector, exact tie
  policy, frozen candidate/raw/auditor hashes, one candidate invocation and
  one separate exhaustive auditor invocation. No container/GPU/model/GUI/live
  task was involved, as specified for this deterministic policy check.
- **D:** All five hand-calculated oracle cases and candidate outputs agreed
  with the separate route-cost enumeration; zero audit errors.
- **C:** This is a newly constructed synthetic schema with two genuinely
  competing endpoints and additive integer millisecond costs. It does not
  decide whether the predecessor's 260 ms endpoint was intended as a route
  competitor or merely a descriptive bound.
- **U:** No original #5851 candidate was rerun; no original or successor
  first-result bytes were changed. No real trace, causal intervention,
  optimization validity, actual latency, product efficacy, GPU/container,
  model, GUI, safety path, or live task is established.

The initial TDD run failed its then-five assertions at the intended missing
candidate API assertion. After implementation, six tests passed, along with
JSON parsing and Python compilation. The max-cost case also passed a separate
construction probe before being included in the frozen five-case candidate.
Preflight command path/assertion errors and the interrupted initial full
checkout are disclosed in `PROCESS.json`; all occurred before the single
candidate/audit pair and did not alter the retained predecessor evidence.

See `PLAN.md`, `FREEZE.json`, exact one-shot `candidate.raw.json`,
`audit.raw.json`, `RUN.json`, `PROCESS.json`, and `SHA256SUMS` for complete
reproduction and provenance.
