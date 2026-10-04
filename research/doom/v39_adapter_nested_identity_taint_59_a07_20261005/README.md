# V39 cross-group nested actuation taint — A07

## H / T / D / C / U

**H.** A copied nested adapter edge with unchanged owner, actuation ID, key and token but altered outer `id` or `step` can split receipt groups and leave the original DOWN/UP pair reported as complete. Every group sharing that nested actuation fingerprint must be tainted.

**T.** Freeze baseline source at commit `de6e56a7bf31792418475e13f1052a6da2974b1e`, current candidate/test bytes, and retained A01 fixture. Test copied DOWN and UP rows, independently changing outer `id` and `step`; rerun earlier duplicate, unknown-event, legacy-transition and A06 token-conflict regressions.

**D.** Baseline must falsely pair the original receipt in all four mutations. Candidate must fail closed for all four and pass all five targeted methods. Exact inputs, hashes and outputs are in `A07_FREEZE.json` and `A07_RESULT.json`. The independent raw-derived audit is `A07_AUDIT.json`.

**C.** Nested `(owner_id, actuation_id, key, intent_token)` is the shared provenance signal in the retained trace. The treatment changes only outer grouping fields.

**U.** Deterministic projector test against one retained synthetic X-adapter trace. This says nothing about live X-server state, physical input release, application consumption, task effect, recovery or MAP01 success. Runtime reported absent swap/cgroup support, so effective memory and swap enforcement is not claimed.

The first attempt used the wrong baseline source and is preserved byte-for-byte as `A07_SUPERSEDED_FREEZE_MISMATCH_WSLC_OUTPUT.txt.gz`; it is excluded from accepted evidence. The corrected runner output is preserved byte-for-byte as `A07_WSLC_OUTPUT.txt.gz`. Both gzip files decompress to their captured terminal output. The corrected run uses the exact Git object named in the freeze.
