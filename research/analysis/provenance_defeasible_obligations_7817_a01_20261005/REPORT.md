# T0 A01 — provenance-checked defeasible obligations

**Status: `PASS_METHOD_SCOPED`.** The frozen candidate and independent audit
each ran exactly once; both exited 0; retries: 0.

The allocation tests a ten-context finite synthetic policy fixture and five
hostile mutations. Construction checks passed 2/2 before freeze and again after
the branch was synchronized with current main. See `PROTOCOL_A01.md` and
`FREEZE.json` for frozen gates and provenance.

The candidate emitted the expected obligation/explanation rows for all ten
contexts. The independent raw-output audit reconstructed all ten decisions and
proof paths with `errors=[]`, then verified all five preregistered mutations
stop with no obligation. These include forged priority issuer, widened scope,
priority cycle, and an explicit attempt to defeat a strict prohibition.

The result supports only agreement for this authored finite semantics and its
specified controls. It cannot establish policy legitimacy, human/source
interpretation, extraction completeness, real-interface safety, or production
authority. No action was dispatched. See exact stdout/stderr and digests in
`RUN.json` and `SHA256SUMS`.
