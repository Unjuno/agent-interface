# Malformed reason values crash the independent class auditor

## H / T / D / C / U

**H.** The class-from-intent verifier should convert every JSON-representable but schema-invalid `yield`/`no_action` reason into an ordinary audit mismatch, rather than allowing malformed values to raise out of the independent auditor.

**T.** Host Windows CPython 3.11.9. Fetched candidate branch `research/qwen5139-current-main-recheck-20260928` at `8869c42a6c5cf2f8e870684431d70b26e1b6e645`; source `audit_results.py` SHA-256 `291e584a643b307651462c383e10a50c2dc74d36383deb9f990f33b28313d978`. Built the existing fixed synthetic construction fixture (formal seed 73194111, support seed 51829177; existing test-only values). Baseline `_dataset_errors` returned zero. Four fresh copies each changed one existing `yield` or `no_action` intent reason in `support_pool` or `heldout_pool` to a JSON object/list. No model, GPU, CUDA, Docker, tokenizer, GUI, or formal allocation.

**D.** `FAIL_AUDITOR_EXCEPTION_ON_JSON_MALFORMED_REASON`: all four malformed cases raised uncaught `TypeError` (`unhashable type: 'dict'` or `'list'`) from membership against the allowed-reason set. A local diagnostic copy added an `isinstance(reason, str)` guard; it returned one ordinary pool class-mismatch error for each malformed case and preserved zero errors on the clean fixture. Exact cases and outcomes are in `result.json`.

**C.** The malformed reason values are valid JSON but violate the intent schema. The observed defect is in the independent auditor's robustness path; it does not establish that the candidate generator emits malformed rows or say anything about model quality.

**U.** Four deterministic fixed cases, one synthetic fixture, one host/Python version. The proposed diagnostic change was not applied to shared PR #5208. Other malformed JSON shapes and full raw-arm audit behavior remain untested.

The initial package-root import failure is preserved separately in `BUILD_FAILURE.json`; the corrected control was run after fixing only that script-path error.
