# #6183 A03 preregistration — scale, outline, and auditor challenges

## Scope and delta

New finite synthetic allocation A03, prospective after A01 infrastructure STOP
and A02 route-only subtest. It keeps A02's four thresholds, pixel/single
baselines, image-only/app-effect separation, and does not overwrite A02. It
adds exact nearest-neighbor 2x scale variants, a closed-outline/hole predicate,
and in-process independent-auditor corruption controls. It remains synthetic;
no application-level effect is claimed.

## H / T / D / C / U

- **H:** Four-threshold topology preserves clear route and outline predicates
  under exact 2x nearest-neighbor scaling, returns UNKNOWN for gray near-touch
  and gray outline closure, and avoids false confident calls better than the
  frozen pixel-distance and single-threshold baselines.
- **T:** One candidate invocation on 20 fixed grayscale images (route and
  outline; base and exact 2x scale); then one independent raw-only auditor
  invocation. Thresholds remain `[64,128,192,240]`. Route uses 4-neighbor
  endpoint reachability. Outline uses count of 4-connected background
  components enclosed from the image boundary. Persistence is PRESENT at
  3-4 matching thresholds, ABSENT at 0-1, UNKNOWN at 2. Candidate sees only
  fixture ids, predicate, pixels, endpoints, and same-scale template id;
  visual truth and hidden graph remain auditor-only. Auditor also executes
  four in-process corruption controls: omitted row, duplicate id, flipped
  visual decision, and fabricated application effect.
- **D:** A03 subtest passes only if all determinate cases are correct, coverage
  is >=75%, near-touch/occluded semantics abstain, exact 2x variants preserve
  classification for the matched predicate, identical-pixel/different-graph
  pair has identical visual outputs and application effect UNKNOWN, persistence
  has strictly fewer false confident calls than both baselines, independent
  replay has zero errors, and all four injected auditor corruptions are
  rejected. Otherwise report the exact FAIL/HOLD; no tuning or retries.
- **C:** Single-threshold connectivity/hole tests may be sufficient for clean
  images; exact application graph/document queries remain the semantic
  reference.
- **U:** Exact nearest-neighbor scaling is not real GUI resampling or
  antialiasing. Small authored rasters do not establish robustness to theme,
  projection, temporal animation, or actual application semantics. App effect
  remains UNKNOWN without an independent app/document oracle.

## Frozen runtime and gates

- Base: `fa791fe937fb24245e785d9e22928b3f4a6a42ae`.
- A03 source freeze commit will be recorded in `RUN.json` and Issue #6183 before
  execution. New package: `formal_a03_orbstack_20261003/`.
- Dedicated VM and private Docker Engine remain `research-6183-t0-20261003`
  (Ubuntu 24.04 arm64; VM 1 CPU/2 GiB). Image remains
  `python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016`.
- Candidate and auditor each run once in separate containers with no network,
  1 CPU, 512 MiB, read-only rootfs, dropped capabilities, user 501:501,
  read-only source and fresh separate output path
  `/home/taka/outputs/topology-6183-a03`.
- Candidate-only input directory contains only `candidate_a03.py` and
  `fixtures_a03.json`; auditor source and labels are mounted separately and are
  not reachable from the candidate container.
- Issue-level METHOD_PASS_SCOPED is still not claimed by A03 alone if the
  later app-oracle/transfer boundary remains untested. No live task or other
  allocation is authorized by this preregistration.
