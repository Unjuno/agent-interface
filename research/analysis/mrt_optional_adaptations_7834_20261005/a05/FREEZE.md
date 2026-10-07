## Prospective moderator-heterogeneity freeze — MRT-7834-A05 (2026-10-05)

This is a new finite-method allocation under this Issue, distinct from A01–A04. It tests subgroup effect recovery under moderator-dependent assignment and whether the pooled average masks effect heterogeneity.

### H / T / D / C / U

**H:** With a pre-treatment binary moderator M and known positivity within each moderator stratum, inverse-propensity assignment contrasts recover the stratum-specific potential-outcome effects. Opposite stratum effects can cancel in the pooled effect and must not be reported as homogeneous. A zero treatment propensity in a stratum, post-treatment moderator timing, or unknown propensity makes the requested moderator-specific contrast NONIDENTIFIABLE.

**T:** Enumerate exactly two moderator strata with potential outcomes M0=(Y0=10,Y1=12), M1=(Y0=20,Y1=19), and assignment probabilities P(A=1|M0)=0.75, P(A=1|M1)=0.25. Each stratum contains its two assignment outcomes with the corresponding assignment mass. Candidate reports both stratum IPW effects, pooled effect, heterogeneity contrast, and all four reconstructed rows. Independent auditor reconstructs rows/oracle separately, checks three NONIDENTIFIABLE gates, and applies seven raw-row mutations. No GUI, model, user data, task action, GPU, network, or product claim.

**D:** PASS_METHOD_SCOPED_A05 only if exactly four rows reconstruct, effects are M0=+2 and M1=-1, pooled effect=+0.5, heterogeneity contrast=+3, and independent audit agrees within 1e-12; all three invalid-identification controls return NONIDENTIFIABLE; seven of seven row mutations are rejected. Otherwise FAIL_METHOD. Environment failure before candidate execution is STOP_ENVIRONMENT with no retry.

**C:** This exact finite fixture assumes known propensities, complete outcomes, fixed potential outcomes, and only two moderator strata. It tests an identifiability/aggregation boundary, not finite-sample precision, moderator discovery, or a treatment recommendation.

**U:** No natural moderator distribution, noisy measurement, multiple testing, adaptive moderator search, carryover, censoring, session interference, actual user behavior, application outcome, or product benefit is represented. Synthetic recovery does not authorize a real-user experiment.

### Frozen inputs and runtime

Base main: c1074c4dc385bae5b94ce93a5870e92c2e6ab07d.
Allocation: MRT-7834-A05-20261005.
Fixture Git blob ea4fbeb68a3346fdb41fa7aab9ef36e8037de65e; SHA-256 a7d45e6fd04cad284e05f69f253b602823e63ce1a9566f08bcb8a0ffa9d64057.
Candidate Git blob 0cfebc79098fc5ca46c884846a53e458f6daa7f0; SHA-256 42f2ac01f71bc5521c9c995224610695c02de5e3f3636d5a064d2d29b58e9610.
Auditor Git blob 6886de9c69085efd1f1f71df82b1d13debc58e1a; SHA-256 1f9395bd680a37f582a7ca9573814cb869e4bf45e1041db1807229a6dd705c95.
Candidate and auditor limits 1/1, attempts 0 before this freeze, no retries. Runtime: WSLc 3.0.1.0, pinned linux/amd64 Node 22 image node@sha256:0a7108bf6c7bf5de370ffb1a3ed6be93d405b43ff159f681a8d18c0e2bc2e402; pull never, network none, one CPU, read-only source/input and separate output directories. Image is cached.