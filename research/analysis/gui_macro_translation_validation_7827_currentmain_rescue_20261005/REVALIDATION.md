# Issue #7827 A05 current-main rescue record

## H — Hypothesis

The preserved A05 finite-model result is worth retaining on current `main` as a method-scoped translation-validation result, provided its immutable evidence and provenance caveats remain visible.

## T — Checks performed

- Copied the exact A01–A05 evidence directories from draft PR #7850 onto a clean branch based on current `main`; no predecessor artifacts were edited.
- A05 construction tests: `python3.12 -m unittest -v test_protocol test_audit` from the A05 directory — 8/8 passed.
- A05 preserved SHA-256 manifest — 15/15 entries match.
- Whitespace inspection reports the historical Markdown hard-break spaces in frozen `SOURCE_PLAN.md` files; these bytes were preserved to avoid changing hash-bound evidence.
- Read the frozen A05 result and independent auditor output: candidate and auditor exit 0; seven registered mutations rejected, five valid pairs accepted, oversized repeat returned UNKNOWN without a certificate.
- Did not rerun the frozen candidate or auditor: `FREEZE.json` explicitly requires one invocation each and prohibits retries. The locally run tests are construction tests, not a fresh formal experiment.

## D — Data and scope

The rescue retains A01–A04 historical failure/HOLD evidence together with A05 and adds this report. The original PR #7850 branch and all frozen blobs remain unchanged. No GUI, model, user input, runtime, or application action is covered.

## C — Conclusion

The retained A05 package supports its recorded finite-model, method-scoped result, and the current-main copy passes the bounded construction/hash checks above. This is not a new formal replay or a broader application-safety result. Keep this successor in draft pending independent review.

## U — Uncertainty / provenance issue

The frozen A05 `FREEZE.json` pins `SOURCE_PLAN.md` by hash, but that file's body still names allocation `UNJUNO-7827-TV-A01-20261005-01` and the A01 additive path, while the A05 freeze/result identify `UNJUNO-7827-TV-A05-20261005-01`. The SHA-256 is internally consistent; the metadata text is not. This rescue preserves the discrepancy rather than rewriting frozen evidence. Reviewers should decide whether the A05 allocation/provenance is sufficiently established before any merge or promotion of the result.
