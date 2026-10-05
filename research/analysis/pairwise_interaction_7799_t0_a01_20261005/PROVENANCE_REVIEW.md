# Post-run provenance review — #7799 A01

## Finding

The first unpublished draft of this follow-up did not hash the retained `candidate.py` or `audit.py`. It checked the candidate and audit JSON outputs, then returned PASS even when run against the older LF-normalized checkout whose `candidate.py` bytes did not match the A01 manifest. That draft's PASS output is discarded and is not evidence.

## Corrected check

The corrected `audit_provenance_v2.py` binds the exact reviewed `FREEZE.json` and `SHA256SUMS`, both frozen source files, the retained candidate and original auditor code, the candidate/audit JSON bytes, and the unchanged HOLD disposition. Seven mutation controls reject altered source/code/manifest/raw bindings. The corrected audit was exercised twice:

- Against the older LF-normalized checkout, it correctly returned `FAIL_SOURCE_BINDING_ONLY` because `candidate.py` hashed to `fa372bfd...`, not the manifest's `acda86fd...`.
- Against a temporary package populated with the exact `candidate.py` bytes from current main, it returned `PASS_SOURCE_BINDING_ONLY` (15/15 checks; 7/7 mutation controls). The fetched file's SHA-256 was `acda86fdfdfc14a1f64339e06dfd134b9c62825a461112839a90e793bddaee3e`, matching the retained A01 `SHA256SUMS` entry.

GitHub main at `a3e6b0c1ab8d6af5c24abb88a451ce41c4ede028` carries the evidence rescue from #8227. The two frozen source files have the same Git blob IDs at that main commit and at the freeze source commit `b5be19963454ce5edafc945b78b100012952dd15`; the retained source-byte checks also pass. The rescued main stores the manifest-matching CRLF `candidate.py`; the older local checkout had normalized it to LF, which is why the corrected check must run against the rescued bytes. The `audit.py`, freeze, manifest, and raw JSON Git blobs match between the local evidence worktree and current main. The original A01 `FREEZE.json`, `SHA256SUMS`, candidate/auditor outputs, and `HOLD_T0_NO_ELIGIBLE_INDEPENDENT_PAIR` are unchanged.

No candidate, original auditor, WSLc job, or formal allocation was invoked. This is a post-run integrity correction only; it does not upgrade the A01 result or prove which bytes the historical WSLc bind mount read.

## Reproduction

From a current-main clone root:

```sh
python research/analysis/pairwise_interaction_7799_t0_a01_20261005/audit_provenance_v2.py \
  research/analysis/pairwise_interaction_7799_t0_a01_20261005 . \
  research/analysis/pairwise_interaction_7799_t0_a01_20261005/results/PROVENANCE_AUDIT_V2.json
python research/analysis/pairwise_interaction_7799_t0_a01_20261005/test_audit_provenance_v2.py
```

The additive `results/PROVENANCE_AUDIT_V2_SHA256.txt` pins the verifier, tests, both dispositions, exact current-main candidate bytes, and every input used here. It leaves the original `SHA256SUMS` unchanged.
