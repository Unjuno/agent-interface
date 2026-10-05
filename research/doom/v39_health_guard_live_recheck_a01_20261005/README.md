# V39 retained live health-guard recheck A01

## H / T / D / C / U

- **H:** The retained V39 run already contains one live instance where an authored health guard invalidated a cover during a pending model turn, discarded the dependent answer, and released all tracked input before the planner terminal. This supports the guard mechanism in that run's source lineage; it does not establish that the chosen threshold reacted early enough for useful control.
- **T:** Recompute the narrow event join from the immutable retained V39 decision report and runtime stream, verify their hashes against the retention manifest, and compare the resulting timing and source closure with current-main requirements.
- **D:** The read-only audit checks decision 5, its source signal, threshold-boundary and invalidating typed observations, planner interruption/discard fields, cover terminal/release, and event chronology. It asserts that the retained source closure used V12 session / V10 input-owner files so it cannot be mistaken for current V15/V12 evidence.
- **C:** One retained live episode; no new game, model, or input allocation. `audit.py` reruns from the repository root and writes the deterministic result to stdout.
- **U:** No per-key release identity, independently useful feedback onset, bounded recovery efficacy, survival benefit, MAP01 exit, or validation of the current V15/V12 startup closure.

## Result

The decision-5 cover was authored from health 61 at sequence 166 with a hard floor of 51. Sequence 200 observed 51 as a soft change, preserving the cover. Sequence 218 observed health 48 and evaluated `below_hard_minimum`. That frame visibly contains an enemy firing toward the player; this is also evidence that the event was threat-exposed, while not locating the initial appearance or damage instant.

The health guard evaluated 9,440.718 ms after the source frame was captured. The cover ended with verified empty keys and buttons 9.727 ms after evaluation. The planner turn terminated as `interrupted`, with its answer ineligible and dependent action discarded, 37.051 ms after guard evaluation. The turn's recorded model duration was 8.916 s. The one-episode independent retained audit passes; the episode ended alive with one kill and no death, but without a MAP01 exit.

The preregistration commit `5ffa6e0716515841575f70b8f0dba32843bf3e98` precedes the result-retention commit `ebb8c7837edf86cc9d02c60bec58828e45fb6c77`. Its 28 pinned source hashes match that earlier Git tree. The runtime manifest contains 20 imported sources; all 20 also match the preregistered tree. Together the records verify 39 unique source paths, including the V39 controller (frozen SHA-256 `cbc44c171f9d83417380af4fb5c06ef7dbf9bb2862c2c40a997bd66f3a985e5e`). Current-main snapshot `b5be19963454ce5edafc945b78b100012952dd15` has a different controller hash, and the run's runtime path is V12/V10 rather than today's V15/V12 composition. This strengthens source identity for the historical V39 run while preserving the need for a fresh current-main test.

The next live experiment must use today's V15/V12 closure and collect per-key release identity, independent useful-feedback timing, and bounded recovery under fresh live threat exposure. This historical result does not justify a threshold change or a broad performance claim.

## Reproduction and identities

```sh
python3 research/doom/v39_health_guard_live_recheck_a01_20261005/audit.py
```

The audit verifies these retained SHA-256 values against `retention-manifest.json`:

- `report.json`: `719db21040b843c5c91c5ff1f3d9fb2051ae1f1e008971547f39f015b4337687`
- `runtime/events.jsonl`: `2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381`
- `runtime/sources.json`: `3bb0fe420f21b682c5739d1e6d1e0ae6996847fceaa5818f0f17a3219437c5f8`
- `runtime/218.png`: `c711f3c36ff56778378a0f82275474615aac9879c2f61ce0d8d4ae8270e5a448`
- `audit-v2.json`: `bb03c350009169283f36c8f0c0a919bb18d46e828ac68b99f40a567d2f141bfc`

The audit also verifies the preregistration and runtime source hashes against the frozen Git tree at `5ffa6e0716515841575f70b8f0dba32843bf3e98`; its ancestor relation to the result commit is checked locally with Git. `RESULT.json` is the retained output from the command. The original result package remains unchanged.
