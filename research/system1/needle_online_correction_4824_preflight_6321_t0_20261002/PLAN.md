# #6321 CPU-only dataset/label preflight

Allocation: `NEEDLE-ONLINE-CORRECTION-4824-CONSTRUCTION-20261002-01`.

## H / T / D / C / U

**H.** A separately implemented raw-only checker will catch a role-label inversion of the sort found in #4824's predecessor before any model fit. It will verify the three new formal seeds' deterministic A-support, B-arrival, and held-out A/B datasets against the frozen target functions.

**T.** Generate data only for seeds `2026100201`, `2026100202`, and `2026100203`. Each seed has A support (32 rows for each value of feature 0), B arrival order (4 rows for each value), A held-out (64 rows for each value), and B held-out (64 rows for each value). Feature vectors are unique within each role/seed across its splits; IDs are unique. Role A target is always class 0. Role B target is class 1 iff feature 0 is 1. Run CPU construction tests before freeze. Freeze generator, independent auditor, test, config, and cached image identities; confirm output absent; then invoke the generator once and the independent auditor once in one network-disabled OrbStack Python container. No optimizer, model, CUDA, GPU, WSLc, GUI, candidate training, retries, or seed substitutions.

**D.** `PASS_LABEL_PREFLIGHT_SCOPED` only if all three exact seeds and all four split inventories match, the feature vectors and IDs satisfy the frozen disjointness/uniqueness conditions, all labels independently match the two role functions, and seven mutation controls are rejected (wrong A label, wrong B label, row deletion, duplicate row, wrong split, altered feature, seed substitution). Any integrity mismatch is FAIL; image/runtime/output gate failure is STOP before data generation.

**C.** This is a deterministic dataset-construction integrity gate, not the model or online-adaptation experiment. It fixes the label-generation regression only; no performance, competence, retention, or adaptation property is measured.

**U.** It does not grant the exclusive RTX 3080 WSLc window. No optimizer updates are run. The image/runtime differs from the eventual WSLc CUDA formal run. All model quality, A-retention, B-acquisition, scope refusal, and GPU execution remain untested.

The formal seeds and generated data are frozen here for later use by the separately authorized formal allocation; they must not be regenerated or altered. This preflight neither consumes GPU authority nor changes #4824 predecessor results.
