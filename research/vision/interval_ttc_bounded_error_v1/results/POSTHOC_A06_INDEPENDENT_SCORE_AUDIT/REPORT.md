# Issue #8157 A06 independent score audit

**Outcome: `STOP_A04_ARTIFACT_MANIFEST_KEYSET_MISMATCH`. No score was produced.** The one scorer invocation verified the three raw files' bytes, then stopped because the A04 freeze's manifest has one additional `first_audit` key. It did not parse the raw JSONL or compute a TTC metric.

The frozen A06 construction checks passed 4/4. The failed initial test-discovery command and corrected successful discovery command are retained in `FREEZE_A06.json`. This diagnostic used native macOS CPython 3.14.5, not a container. No candidate, generator, A02/A03/A04/A05 auditor, model, GUI, or input action was run.

Prior outcomes are unchanged: A02 `FAIL_METHOD` with scientific comparison unscorable; A03 `STOP_AUDITOR_RUNTIME_ERROR`; A04 `PASS_RAW_RECONCILIATION_ONLY`; A05 `STOP_BEFORE_INPUT_READ_ARGUMENT_ROOT_MISMATCH`. A06 is a retained harness STOP only and does not test whether interval TTC improved on point TTC.
