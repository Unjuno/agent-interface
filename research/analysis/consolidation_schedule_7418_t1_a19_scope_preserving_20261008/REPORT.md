# T1-A19 construction report — PASS_CONSTRUCTION_SCOPED

## Result

The deterministic candidate/auditor construction check passed 13/13 tests on host CPython 3.14.5 on macOS, including after the decision-label revision. The mock round trip exercised 390 candidate API-call slots and produced 720 individually scored answers; the independent raw-only auditor reconstructed all transitions and returned `PASS_METHOD` with zero errors. Its exact mock answers had no schedule contrast, so the updated descriptive label is `NO_10PP_CONTRAST_OBSERVED_SCOPED`. A new negative control made exactly six valid-shaped answers wrong in one arm for each seed; the auditor reported the boundary contrast as `0.1` in all three seeds and returned `OBSERVED_CADENCE_CONTRAST_SCOPED`. These mock outcomes test the constructed runner/oracle and threshold wiring only; they are not model results and carry no cadence inference.

The suite also confirmed that a missing `mode` scope is rejected even when the value and source ID remain correct; the same action under a mismatched scope yields `UNKNOWN`; hidden ledger truth is not used to score an empty summary; conflicts appear only after both matching observations arrive; a retained raw mutation that removes scope is rejected by the full auditor; prompt drift is rejected; and a preloaded model stops before raw creation or inference. A valid-shaped wrong answer lowers accuracy without failing the method gate; an invalid answer schema fails the method gate.

## Reproduction

From this directory:

```sh
PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest -v test_construction.py
```

The suite mocks the model API. No candidate model request, private preflight, formal auditor invocation, or formal allocation was performed. The temporary JSONL created by the mock test is deleted by the test harness; the test code and output are the reproducible construction evidence.

## Runtime and scope

The host is macOS. The OrbStack Docker Engine Unix-socket `_ping` timed out with curl exit 28 and HTTP 000; no container image digest or isolated-runtime preflight is available. Host execution is recorded without an isolation claim. Disk free-space readings varied from 194 MiB to 6.5 GiB in this turn, and system free memory was 15% at the latest memory-pressure read. The model store and running services were left untouched. No model calls were started.

At 2026-10-08 14:58 JST, a read-only follow-up found OrbStack and its VM manager processes present, but the Docker socket still timed out (3.002 s, zero response bytes) and no private listener existed on port 11435. `ollama list` showed the existing system tag `qwen3:14b` with ID prefix `bdbd181c33f2`. The package's store checker confirmed the local manifest digest equals the frozen digest and all four manifest layers exist at their declared sizes; it did not recompute blob content hashes or contact the private endpoint. One `df` read showed 5.1 GiB free. These observations do not qualify an isolated runtime or establish stable capacity, so the formal hold remains.

A follow-up `df` about 32 seconds later showed 336 MiB free. The 5.1 GiB observation was therefore transient; capacity remains unqualified. No cleanup, daemon restart, alternate endpoint, or inference was attempted.

The read-only `orbctl status` probe also produced no output and remained blocked for at least 17 seconds. I sent SIGTERM only to that probe process; OrbStack and VM manager processes were not stopped. This adds no evidence of Docker readiness.

`orbctl doctor --quiet` exited 0 but reported that the active `docker` and `docker-compose` executables resolve to Nix paths rather than OrbStack's wrappers. Running OrbStack's own Docker wrapper directly returned client version 29.4.0, then failed connecting to the configured OrbStack socket with EOF on `/v1.54/version`. The PATH warning is recorded, but a one-shot wrapper call did not restore Engine access; no `--fix`, PATH change, daemon restart, or other runtime repair was performed.

This construction PASS only shows that the frozen design can express scope-preserving claims, visible-evidence scoring, fixed query batches, and one-shot raw/audit gates in a mock. T1 remains unrun. The protocol explicitly leaves formal freeze and inference pending a pinned eligible runtime, stable resource headroom, and exact model preflight.

## Pre-freeze decision-gate calibration

The separate simulation at `decision_gate_calibration_20261008/` evaluated the exact six-pair, three-seed, 10-percentage-point rule over 200,000 allocations per scenario. Under an equal 0.50-accuracy null, the rule labeled a sensitivity contrast in 4.16% of independent-answer simulations (Monte Carlo SE 0.045 percentage points) and 43.68% of perfect-prefix-cluster simulations (SE 0.111 percentage points). For one arm with true accuracy +0.10 over the other three, the sensitivity-decision rate was 34.65% under independent answers (SE 0.106 percentage points) and 49.77% under perfect prefix clusters (SE 0.112 percentage points). At +0.20 it was 92.85% and 65.61%, respectively.

The predeclared calibration rule flags the decision gate because +0.10 detection is below 50% in the independent-answer model. The cluster-null rate also shows strong dependence on within-prefix correlation. This is an idealized simulation, not an estimated Qwen3 error rate. The numerical threshold is unchanged, but the auditor labels were narrowed to `OBSERVED_CADENCE_CONTRAST_SCOPED` and `NO_10PP_CONTRAST_OBSERVED_SCOPED`; they describe these finite observations and explicitly do not claim significance, equivalence, or general cadence effects.

The independent exact-PMF audits in `decision_gate_calibration_20261008/` first verified a single-pair lower bound and exactly enumerated the full six-pair equal-accuracy null union. The null rates were 4.1555% for independent answers and 43.5984% for perfect prefix clusters, matching Monte Carlo estimates (4.1615%, 43.6795%) within 0.13 and 0.73 Monte Carlo standard errors. A further exact Binomial-state enumeration cross-checked all four non-null power cases: +0.10 gave 34.5737% iid and 49.7283% clustered; +0.20 gave 92.8598% iid and 65.4230% clustered. Each differed from its Monte Carlo estimate by less than 1.80 standard errors. This validates the simulation arithmetic under its stipulated independent arm/seed Binomial model; it does not estimate actual model dependence or cadence effects.
