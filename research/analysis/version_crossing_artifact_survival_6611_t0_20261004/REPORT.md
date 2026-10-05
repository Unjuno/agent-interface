# Issue #6611 T0 — version-crossing artifact-survival scorer

## Disposition

`PASS_METHOD_SCOPED`. The frozen synthetic candidate emitted two initially
passing routes and 18 later-reader rows (7 PASS, 9 FAIL, 2 UNKNOWN). The
independent auditor reconstructed every row with zero errors and rejected all
four preregistered corruptions. Candidate/auditor/retry counts were 1/1/0.

## H / T / D / C / U

- **H:** A finite scorer can separate initial contract success from later
  reader survival, identify planted loss of significant properties, preserve
  harmless cosmetic changes as PASS, and mark missing dependency evidence
  UNKNOWN; a synthetic route-cost ranking reversal is possible.
- **T:** Two synthetic routes × nine deterministic reader cases, with exact
  initial property gates, independent later scoring, and four corruption
  controls.
- **D:** Both routes matched the exact initial property contract; all 18
  future rows matched the independent oracle; formula/link/render loss and
  reader-open failure were FAIL; cosmetic-only change was PASS; unavailable
  dependency was UNKNOWN; the route ranking reversed in the stipulated
  survival case; all four corruptions were rejected.
- **C:** A strict current contract may already capture all significant
  properties, making later-route choice irrelevant. Native format or ordinary
  backup may be sufficient.
- **U:** No real artifacts, formats, applications, readers, renderers, or
  migrations were exercised. This is scorer sensitivity only—not a
  compatibility, durability, or long-term preservation result.

## Result detail

Both routes passed all five initial synthetic properties. Later cases scored
7 PASS, 9 FAIL, and 2 UNKNOWN. In the planted route reversal, the fast route
failed formula survival at a stipulated cumulative cost of 120 ms, while the
durable route survived at 60 ms; this is only arithmetic under the fixture's
synthetic costs. Hash and transport success were not treated as semantic
success. Four independently checked corruptions were rejected.

## Execution and evidence

- Host-only CPython standard library; no model, network, user artifact, app,
  GUI, external reader, or container. OrbStack was not retried because the
  permitted scope is a deterministic scorer and the earlier cached-blob
  container path was unavailable.
- Frozen source commit: `5532bbcea`; frozen base: `5d5748a85816297905ba16bbc0b342e41af22559`.
- Candidate command: `python3 -B candidate.py --out formal_01/raw.json`
  (exit 0). Auditor command: `python3 -B auditor.py --raw formal_01/raw.json --out formal_01/audit.json`
  (exit 0). No retries.
- Construction and final focused tests: 2/2 pass. The sparse-checkout CI
  entry point passes 2/2 tests (including this package), the retained analysis
  index passes at 663/663, all package manifest hashes verify, and
  `git diff --check` passes.
- A broader local replay of 44 archival workflow unittest commands had 39
  clean exits. Three archival directories reported no discoverable tests, one
  pinned-source test pair expected the older workflow SHA before CI's explicit
  historical-workflow restore step, and the live-control test directory is
  absent from this local checkout. These do not change the package result;
  full remote CI remains the integration gate.
- Raw and audit outputs, one-shot custody, and SHA-256 manifest are retained
  in [`formal_01/`](formal_01/).

## Next boundary

The method gate is closed only for this synthetic scorer. Any claim about
actual version compatibility requires separately authorized, disposable real
artifacts and named reader/version pairs with independently defined semantic
properties. This result does not authorize that experiment.
