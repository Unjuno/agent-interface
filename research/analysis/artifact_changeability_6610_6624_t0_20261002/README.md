# Issue #6624 T0 — post-success artifact changeability

## H / T / D / C / U

**H.** Two routes can produce the same initially correct visible artifact while preserving different structure. A literal/raster route should be cheaper for no-follow-up and simple pixel/style-only cases; a structure-preserving route may avoid reconstruction or refusal for later semantic edits. A cost-aware route choice can reverse with the declared follow-up mix. This is a synthetic assay hypothesis, not a product claim.

**T.** Six finite cases exercise both routes (12 raw rows): spreadsheet none/style/formula-rebuild; drawing none/pixel-edit/move-front-while-preserving-occluded-underlay. The initial contract requires visible parity only, not native editability. The spreadsheet's later request explicitly supplies `SUM(A,B)` and two source updates, allowing the flattened route to rebuild the formula at abstract cost. The drawing's raster route cannot recover hidden red underlay pixels after moving the blue front object, so it must return UNKNOWN; native objects preserve the underlay. The candidate sees only `cases_public.json`; a separate `oracle_truth.json` drives the independent raw auditor. `costs.json` is fixed external-to-code abstract operation weighting; it is not time, user effort or an observed application cost.

**D.** `METHOD_PASS_SCOPED` requires exact initial render parity for both representations; correct formula/effect and unaffected drawing pixels; flat raster UNKNOWN rather than hidden-layer fabrication; native-object preservation; route-ranking reversal between the two declared spreadsheet mixtures; flat preference for drawing's no-structure/pixel-only mixture; and rejection of seven raw corruptions. Any wrong or collateral effect is `FAIL_AUDIT`.

**C.** The route distinction may vanish when initial task contracts require editability, and flat artifacts can sometimes be reconstructed cheaply. Conversely, a future edit may be impossible from raster alone. The selected abstract weights are illustrative and can determine a cost ranking.

**U.** No real spreadsheet/slide/drawing application, agent/model, user artifact, actual edit time, follow-up prevalence, user preference, or durability was tested. The result is limited to this exact finite simulator; abstract cost units are sensitivity inputs, not measurements. No T1/product/efficiency claim follows.

## Execution protocol and outcome

- Allocation `ARTIFACT-CHANGEABILITY-6624-T0-HOSTCPU-20261002-01`; base main `d9e2448e6dd53e36a2ac9352c09e0bfd39f971f7`; branch `research/artifact-changeability-6624-t0-20261002`.
- Local host: Windows, CPython 3.11.9, standard library only. WSLc/Docker/GPU were not invoked: this deterministic CPU-only model has no container/API requirement, while shared runtime work was concurrently active. No shared service/process was touched.
- First construction test attempt exposed a scorer key error (6 tests, fail before any raw output). It was fixed during construction only. Second construction suite passed 6/6, including seven corruption mutations.
- Immediate formal start gate: main equals frozen base; branch equals the frozen research branch; source/input hashes match `FREEZE.json`; output paths absent. Candidate and independent auditor each have one invocation; retry budget zero.
- Candidate and auditor run only from an isolated copy of this package; output names are collision-guarded. The candidate does not load the hidden oracle. All raw/failed attempts are retained; no model, GPU, CUDA, optimizer, GUI, network or user input.

## Preregistered abstract operation costs

| Family / scenario | Flat/raster | Structured/native | Preferred |
|---|---:|---:|---|
| Spreadsheet low-change mix | 2.0 | 3.5 | Flat |
| Spreadsheet structure-heavy mix | 6.8 | 4.1 | Structured |
| Drawing no-follow-up/pixel-only mix | 1.3 | 4.6 | Raster |
| Drawing underlay-preserving object move | Ineligible (UNKNOWN) | 5.0 | Native |

These are deterministic sums of declared unit weights, not measured costs. Correctness eligibility is checked before cost comparison; UNKNOWN is never treated as a cheap successful edit.

## Exact reproduction

From this directory:

```powershell
python -m unittest -v test_method.py
python run_candidate.py candidate_raw.json
python run_audit.py candidate_raw.json audit.json
```

The formal output files are created only once and are preserved with their SHA-256 values in `SHA256SUMS`.
