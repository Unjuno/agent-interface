# Issue #6600 practice-order discriminator T0 A01

## H / T / D / C / U

- **H:** At fixed task dose, demonstrated facts, support offers, hint profile, stop/skip rights, effect truth, and assessment history, blocked versus mixed practice order is the only schedule difference. This T0 does not predict which order is better.
- **T:** Construct two six-slot ledgers from the same six task IDs: `A1,A2,B1,B2,C1,C2` and `A1,B1,C1,A2,B2,C2`. Independently reconstruct both ledgers and inject six corruption cases.
- **D:** Method-scoped pass requires exact source-byte binding, exact reconstruction of both arms, equal task multiset, equal assessment history, zero execution counters, zero forbidden effects, and rejection of all six mutations.
- **C:** No participants, allocation, task actions, learning outcomes, or external effects. This is not evidence that either schedule improves learning or safe completion.
- **U:** Human T1 requires a separately reviewed protocol, authorization, consent/safety review, and its own allocation. This package does not authorize it.

## Reproduction

Run construction tests before any one-shot formal invocation:

```sh
python3 -m unittest discover -s research/analysis/faded_demonstration_practice_order_6600_t0_a01_20261008 -p 'test_contract.py' -v
python3 -m py_compile research/analysis/faded_demonstration_practice_order_6600_t0_a01_20261008/candidate.py research/analysis/faded_demonstration_practice_order_6600_t0_a01_20261008/audit.py
```

The frozen candidate and independent auditor, if formally invoked, each run once against the preregistered `SOURCE.json` and `ORACLE.json`; capture stdout, exit status, and output hashes without rerunning. Formal commands and resulting hashes must be preregistered on Issue #6600 before invocation. Do not interpret the unit tests as the formal candidate/auditor run.

## Execution boundary

This is a deterministic stdlib-only ledger construction; there is no model, network, GUI, simulator, participant, or host-state dependency. A Docker content-store inspection problem was observed during intake, but the T0 itself does not require container isolation. Any future effectful or human-facing experiment requires a suitable isolated environment and separate authorization.
