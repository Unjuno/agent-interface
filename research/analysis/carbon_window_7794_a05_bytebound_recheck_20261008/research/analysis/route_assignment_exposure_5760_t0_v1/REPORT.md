# Issue #5760 T0 — assignment versus selected exposure

Date: 2026-10-01  
Disposition: `PASS_METHOD_SCOPED`  
Scientific status: constructed finite-table method check; not empirical or causal evidence.

## H / T / D / C / U

**H.** When local-route exposure depends on difficulty, conditioning on episodes that actually execute local actions can distort the contrast between whole assigned policies. An assignment–exposure ledger should retain all assigned rows, fallback costs, and label the selected subset as descriptive.

**T.** A frozen four-task positive reversal and a four-task exposure-independent null were expanded to both assigned arms (16 rows total). A separately hard-coded oracle independently reconstructed every row and recomputed the policy and selected-subset contrasts. Six mutations tested denominator loss, timing relabeling, fallback-cost deletion, causal overclaim, null-control corruption, and summary forgery.

**D.** `PASS_METHOD_SCOPED` required exact agreement for both contrasts and rejection of all six mutations. Candidate and auditor each ran once in separate network-disabled Docker containers. The outcome is limited to the synthetic finite table.

**C.** Deterministic constructed examples establish only that the ledger arithmetic and guards detect this specified pattern. They do not show that any prior or live comparison is biased, nor that this contract alone suffices for all adaptive routes.

**U.** Randomized route allocation, interference, real initial-state alignment, real acquisition/guard/fallback/recovery costs, censoring, and independent GUI task effects were not tested. No causal ITT, mechanism effect, model, runtime, safety, or product claim follows.

## Frozen source and environment

- Issue: [#5760](https://github.com/Unjuno/agent-interface/issues/5760)
- Source main commit: `9bf253feba4a615f0b58c563d575b4b0a4a84f8b`
- Branch: `research/5760-assignment-exposure-t0-20261001-junny`
- Allocation: `5760-route-assignment-t0-20261001-01`
- Candidate: `python runner.py` (one invocation)
- Independent auditor: `python audit.py /in/raw.json` (one invocation)
- Docker Desktop 29.8.0, Linux/amd64; image `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`; `--network none --cpus=1 --memory=256m --pids-limit=64`.
- Both containers exited 0; Docker inventory was empty after execution.

| Frozen input | SHA-256 |
|---|---|
| `runner.py` | `419C66FA982700254F1DCB57AF45AA11F34602B49526F2E5641F629D76834413` |
| `audit.py` | `0B150EFAAF0494BCB3F83A86F2715FB5279AE6DD4111966AD0F0508B899D8D69` |
| `fixture.json` | `44E3A2D63EA8B77048CC378921DBBE5E25107E45CF4BFCD344487B343E17D162` |
| `test_preflight.py` | `A4E231AFB11D4F4F201832B2ECFF41174A3B5CE2EF9F802F89709A11A5679BF7` |

## Result

| Scenario | A assigned success / time | B assigned success / time | A−B assigned | A-local-only minus B (descriptive) |
|---|---|---|---|---|
| Constructed selection reversal | 2/4; 5.5 | 4/4; 5.0 | success −0.5; time +0.5 | success 0; time −4.0 |
| Exposure-independent null | 4/4; 4.0 | 4/4; 5.0 | success 0; time −1.0 | success 0; time −1.0 |

The positive fixture demonstrates the intended distortion: the selected local subset omits two hard failed fallback rows and makes A appear four time units faster, although its complete assigned policy is half a unit slower and has a lower success rate. The null control shows no such selected-subset discrepancy. All 16 rows and fallback costs remain in the raw artifact.

Independent auditor: exact rows and summaries matched its separately hard-coded oracle; `errors=[]`; all 6/6 corruption controls rejected; `PASS_METHOD_SCOPED`.

## Retained artifacts

- `fixture.json`: frozen potential-outcome fixture.
- `runner.py`: candidate materializer.
- `audit.py`: independent raw-only audit and mutation suite.
- `outputs/formal01/raw.json`: candidate raw rows and summaries; SHA-256 `7318AD6E5E1E3646C4BE471416019C5FB8826B7560D49473E8BABA44ECF2165A`.
- `outputs/formal01/audit.json`: compact independent audit; SHA-256 `44421B6DC901FB8E4D99843500BD1FD678A61525EA7C1E102632AD61A410C328`.
- `outputs/formal01/execution.json`: commands, environment, exit codes, source/output hashes; SHA-256 `931C1138F8F411309409D6DAFE23723EEC5A6575816C0F3BFEB1575ABCD5F899`.

No predecessor or prior result was changed. T1 would require a separate authorized prospective assignment with frozen policies, independent task effects, complete all-attempt accounting, and explicit interference/causal assumptions; this T0 grants no such allocation.
