# Construction dose-check audit receipt

Disposition: `PASS_INDEPENDENT_REPLAY` for the host-only construction artifact only. This is not the frozen candidate run or formal auditor invocation.

## Inputs

- Corrected construction script SHA-256: `98ec1814bcddebb679fb616b7f8f76f75a517f0ad19755336904749e9c06aa5f`
- Corrected dose-check JSON SHA-256: `32d3ccaa832ba189dc380d37e5aa10f988f2892f6d956d48dff61f60425d6da8`
- Immutable invalid predecessor JSON SHA-256: `32d3ccaa832ba189dc380d37e5aa10f988f2892f6d956d48dff61f60425d6da8`
- Fixture SHA-256: `163f85659dabb59861627f4641d6df211d45a1965352d5d5e2e3f396b39256ab`
- Canonical runner SHA-256 (unchanged): `d332bea86527efc1c08f84fc4a0760f7bc41ed2fc07a1da38d13cfda2c418c15`

## Method and outcome

The audit imported only `audit.py`'s independent event equations. For each of the 14 declared doses, it reconstructed each load × mechanism × episode in both arms from the fixture, replacing only `probe_units`. It compared target eligibility, every target probe/no-probe loss tick, the median paired advance, and all three no-loss-control counts (pairs, no-probe losses, probe losses, probe-created losses). All 14 rows and 14 × 90 paired episodes matched exactly; no errors.

| Probe units | Median target advance (ticks) | Probe-created losses in 54 control pairs |
|---:|---:|---:|
| 1, 2, 3, 4, 6, 8 | 0 | 0 |
| 12 | 0 | 6 |
| 16 | 32 | 19 |
| 20 | 48 | 36 |
| 24 | 60 | 49 |
| 28, 32, 36, 40 | 64 | 54 |

The first artifact, despite a coincidentally identical file digest after rerun, is preserved by its distinct filename and is considered invalid based on the audit failure. Root cause: the construction code changed the fixture object but `runner.build()` used a module-global fixture path to compute the raw fixture hash; this caused each dose's candidate pairs to be generated from canonical 40-unit input. The corrected code binds the intended fixture path during each build. The original and corrected JSON share the same digest because JSON output contains the same allocation/fixture identity and, before the bug fix, the mistakenly repeated 40-unit data exactly equalled the corrected 40-unit row. Treat the filename, source version and audit history—not the digest alone—as the predecessor distinction.

Command used for the separate replay was a one-off host Python process, not Docker/OrbStack and not a candidate/auditor allocation:

```sh
python3 - <<'PY'
# Imported audit.py.expected_arm; independently reconstructed all 14 dose rows
# and checked exact target ticks/median/eligibility and all control counters.
PY
```

Scope: deterministic analyst-authored fixture only. No probabilities, external validity, product, live-agent, or repeated-probe safety claim.
