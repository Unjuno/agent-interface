# Issue #59 intermittent-observation YIELD guard — T0 result

**Disposition: `PASS_SYNTHETIC_GUARD_CONTRACT_SCOPED`.** This finite synthetic allocation exercises a continuation guard during a delayed planner call. It does not test the game, a runtime controller, model behavior, actual input release, survival, or MAP01 progress.

## H / T / D / C / U

- **H:** A continuation policy that treats sequence freshness as sufficient can continue through health loss or unverifiable observation state; a fail-closed YIELD guard should distinguish fresh-stable continuation from loss, stale sequence and ambiguous time evidence without granting input authority.
- **T:** From source `c4d2d4b1ccf4512ec79af75bd8eaecfcada39947`, run a frozen finite table of ten typed-observation cases through a candidate state predicate. Independently reconstruct every expected disposition from raw rows and test six corruption controls. Candidate and auditor each invoked once; no retries.
- **D:** Candidate emitted 10/10 rows: two `CONTINUE`, eight typed `YIELD_*`. Independent raw-only audit returned `PASS_SYNTHETIC_GUARD_CONTRACT_SCOPED`, errors `[]`, and rejected 6/6 mutations. All YIELDs terminate the current cover, require a separate fresh admission before any new plan, and grant no input authority.
- **C:** macOS arm64 host, CPython 3.14.5, standard library. The deterministic truth table did not require container-dependent semantics. OrbStack inventory showed a long-running `unjuno-native-ci-6092` container and an unrelated running VM; no exact transferable exclusive lease was available, so no container was started or changed. No game, model/provider, GUI, input, GPU, network, or external effect.
- **U:** The model is authored and finite. It does not establish that an actual monitor observes these states, that a backend releases held keys promptly, that YIELD improves task outcomes, or that this predicate is sufficient for MAP01/other environments. The earlier #59 live T1 remains separately held and is neither authorized nor consumed.

## Frozen cases and result

| Input condition | Decision |
|---|---|
| New sequence, ordered observation, same health | `CONTINUE` |
| New sequence, health loss 85→73 | `YIELD_HEALTH_LOSS` |
| New sequence, health gain | `CONTINUE` |
| Sequence not newer than source | `YIELD_NON_FRESH` |
| Observation/health missing | `YIELD_OBSERVATION_MISSING` |
| Health unavailable or malformed | typed `YIELD` |
| Incomparable clock domain | `YIELD_CLOCK_DOMAIN` |
| Capture interval after availability | `YIELD_CAPTURE_NOT_AVAILABLE` |
| Capture interval straddles decision time | `YIELD_CAPTURE_ORDER_UNKNOWN` |

The last two boundary cases were added to expose a subtlety: a newer sequence number is not by itself proof that its capture preceded the decision. The construction suite caught a boundary mismatch before the formal candidate/auditor run; the fixture/oracle boundary was corrected, then all four construction tests passed before freezing and executing the formal pair. This is retained as construction history, not a formal retry.

## Reproduction

From this directory, using a fresh empty output directory only:

```sh
python3 -B -m unittest discover -p 'test_*.py' -v
python3 -B candidate.py
python3 -B audit.py
sha256sum -c SHA256SUMS
```

The current one-shot output directory is occupied. Do not rerun this allocation. The frozen fixture, candidate, auditor, raw candidate result, independent result, and source identities are recorded in `FREEZE.json`, `RUN.json`, and `SHA256SUMS`.
