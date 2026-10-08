# Issue #6422 T0 — denial-aware request policy

## H / T / D / C / U

**H (finite method hypothesis).** On this authored no-effect fixture, an effect-aware denial ledger blocks equivalent follow-up approval requests despite a new request ID, paraphrase, changed route, narrowed-looking wording, alternate non-veto principal, or elapsed time; it still permits a new confirmation request after a materially changed effect, authenticated user reopening, no response, or an independently verified explicitly stated deferral condition. A deferral condition can make a fresh request eligible; it never authorizes the effect. Safety cancellation/release remains available.

**T.** Compare 14 frozen histories under three policies: ID-only retry, a one-follow-up prompt-count cap, and the denial ledger. The fixture includes the cases listed in `fixtures.json`; it is synthetic, finite, and contains no actual user, approval, model, UI or task effect. Run the construction suite, then one candidate CLI invocation, then one independent raw-only auditor invocation. The auditor reconstructs decisions and independently rejects four mutations (erased denial, forged reopening, changed required-principal mapping, hidden effect component).

**D.** `PASS_METHOD_SCOPED` iff all 14 raw rows reconcile to the frozen fixture, the denial ledger has zero equivalent re-ask bypasses and zero blocks among the four legitimate fresh-request cases, cancellation/release remains allowed, and all four corruption controls are rejected. Any row, decision or corruption mismatch is `FAIL_METHOD`; missing/unverifiable fixture or provenance is `HOLD`. The controls are descriptive: ID-only should allow the new-ID equivalents, while the count cap should suppress legitimate changed/reopened/eligible requests.

**C.** A trusted-path typed DENY plus a simple instruction may suffice; a count cap might be adequate if there are no legitimate re-openings or changed effects. Effect equivalence may be too ambiguous to classify safely.

**U.** This tests policy mechanics on hand-authored records only. It does not measure model proposals, user pressure/coercion, human behavior, GUI state, authority correctness in a live system, or real effect prevention. No general H claim, production authorization, or T1 permission follows.

## Frozen provenance and execution boundary

- Scientific issue: open Issue #6422; its current denial-scope refinement distinguishes `DENY_EFFECT`, source-stated `DEFER_UNTIL`, `NO_RESPONSE`, and `UNKNOWN_SCOPE`.
- Frozen repository main at source preparation: `f56a816bd346790255011b4fc0020ad10c52bedd`.
- Additive package: `research/analysis/denial_aware_request_6422_t0_20261002_v1/`.
- Source/input freeze hashes are in `FREEZE.json`; outputs are not inputs and will be added only after the one-shot candidate/audit.
- Local execution is host-only CPython 3.11.9 on Windows CPU. At preparation, shared WSLc listed three unrelated exited containers and its session processes were present. To avoid touching another task's container/runtime, this T0 does not invoke WSLc, Docker, WSL or GPU; no model/GPU is needed for this finite rule-mechanics test. This is a recorded environment deviation, not container evidence.
- Exact construction command: `python -m unittest discover -s research/analysis/denial_aware_request_6422_t0_20261002_v1 -p 'test_*.py' -v`.
- Formal candidate command: `python research/analysis/denial_aware_request_6422_t0_20261002_v1/candidate.py --input research/analysis/denial_aware_request_6422_t0_20261002_v1/fixtures.json --output research/analysis/denial_aware_request_6422_t0_20261002_v1/candidate_output.json`.
- Formal audit command: `python research/analysis/denial_aware_request_6422_t0_20261002_v1/audit.py --input research/analysis/denial_aware_request_6422_t0_20261002_v1/fixtures.json --raw research/analysis/denial_aware_request_6422_t0_20261002_v1/candidate_output.json --output research/analysis/denial_aware_request_6422_t0_20261002_v1/audit_report.json`.
- No retry, prompt/model run, real user contact, live approval, external workflow experiment, container change, or GPU operation is in scope.
