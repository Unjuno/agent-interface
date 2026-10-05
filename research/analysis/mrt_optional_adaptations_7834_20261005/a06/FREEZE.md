## Prospective moderator-heterogeneity successor freeze — MRT-7834-A06 (2026-10-05)

A05 remains a consumed FAIL_METHOD in comment #5986643544. A06 corrects its shared denominator defect and auditor extra-key blind spot. This is a fresh source-bound allocation, not a rerun or relabel of A05. A05's first result and A06's pre-freeze construction probes are preserved append-only.

### H / T / D / C / U

**H:** With a pre-treatment binary moderator, known moderator-specific treatment propensities and positive support in each stratum, assignment-probability weighting recovers stratum potential-outcome effects. Opposite effects can partially cancel in the pooled average, so the pooled result cannot stand in for subgroup effects. Zero treatment support, post-treatment moderator timing, and unknown propensity make the requested stratum contrast NONIDENTIFIABLE.

**T:** Enumerate two equally weighted moderator strata: M0 potential outcomes (A0=10,A1=12), P(A1|M0)=0.75; M1 (A0=20,A1=19), P(A1|M1)=0.25. Each stratum's two assignment rows carry their assignment probability mass. Candidate reports exact rows, both stratum IPW contrasts, equal-stratum pooled effect, heterogeneity contrast, and decisions for three frozen support/timing controls. Auditor independently reconstructs all four rows and potential-outcome contrasts; it rejects seven raw-row mutations, including extra keys.

**D:** PASS_METHOD_SCOPED_A06 requires exactly four expected rows; M0=+2, M1=-1, pooled=+0.5, heterogeneity M0−M1=+3, all within 1e-12; exactly three NONIDENTIFIABLE control outcomes; exact candidate/auditor agreement; and 7/7 mutations rejected. Any mismatch is FAIL_METHOD. Pre-execution image/source/mount failure is STOP_ENVIRONMENT and consumes the one frozen attempt; no retries.

**C:** This is a two-stratum deterministic finite construction with known assignment probabilities, complete outcomes, and fixed potential outcomes. It examines effect aggregation and identification, not a sampling distribution or moderator discovery.

**U:** It omits natural moderator prevalence and measurement error, multiple testing, adaptive moderator search, carryover, censoring, session interference, actual user behavior, task/application outcomes, and product benefit. It gives no authorization for a real-user intervention and has no GPU requirement.

### Frozen source and runtime

Freeze base main: 88d875cc0916accb1a5fa36057253686f0586f1e.
Fixture Git blob 3229b1167a3bf79ef994923bd095f258ff50f258; SHA-256 fdc86e6276c88dfe6ade949a013ec676b95be59ea1242d8a78b5cfca9dd28deb.
Candidate Git blob 7832efe701e4bb9a7ca0670bb6e8fc0a7b9ec295; SHA-256 16df535c69cf95b9d7f9bf868765eed0938b82c26293edb315358d46630440b6.
Independent auditor Git blob 311ee4954f945a802301073f8c7dea13c0d02b42; SHA-256 9b6046a51aad9ddf8e3aa4b9a15669d6fc42693e0fe8150995240a8054d6a96b.
Pre-freeze probe outcomes and cwd failure are retained at construction blobs 6b16f12c7dadc903524f5f495b1b59ca22224d40, 45c61675f828e010785b7322f1bc789ae374c889, e69de29bb2d1d6434b8b29ae775ad8c2e48c5391, and 940718d2267da4f393fd9860f876cb7723dc2433.

Runtime: WSLc 3.0.1.0, linux/amd64 node@sha256:0a7108bf6c7bf5de370ffb1a3ed6be93d405b43ff159f681a8d18c0e2bc2e402 (Node v22.23.3), cached image, pull never, network none, CPU 1, disposable container, source/input read-only, separate candidate/audit output mounts. Formal execution counts at freeze: candidate 0/1, auditor 0/1, retries 0.

Candidate command:
wslc.exe run --rm --pull never --network none --cpus 1 --volume "C:\Users\junny\Documents\Codex\2026-09-19\new-chat\_tmp\mrt7834-a06-20261005\src:/src:ro" --volume "C:\Users\junny\Documents\Codex\2026-09-19\new-chat\_tmp\mrt7834-a06-20261005\candidate-out:/out" --workdir /src node@sha256:0a7108bf6c7bf5de370ffb1a3ed6be93d405b43ff159f681a8d18c0e2bc2e402 sh -lc "node candidate.js > /out/candidate.json"

Auditor command:
wslc.exe run --rm --pull never --network none --cpus 1 --volume "C:\Users\junny\Documents\Codex\2026-09-19\new-chat\_tmp\mrt7834-a06-20261005\src:/src:ro" --volume "C:\Users\junny\Documents\Codex\2026-09-19\new-chat\_tmp\mrt7834-a06-20261005\candidate-out:/input:ro" --volume "C:\Users\junny\Documents\Codex\2026-09-19\new-chat\_tmp\mrt7834-a06-20261005\audit-out:/out" --workdir /src node@sha256:0a7108bf6c7bf5de370ffb1a3ed6be93d405b43ff159f681a8d18c0e2bc2e402 sh -lc "node auditor.js > /out/audit.json"