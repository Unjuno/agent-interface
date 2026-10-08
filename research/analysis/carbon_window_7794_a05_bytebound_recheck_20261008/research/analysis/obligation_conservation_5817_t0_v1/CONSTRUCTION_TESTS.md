# Construction-only test record

These are local Windows construction checks, separate from the frozen Docker allocation. Runtime: Python 3.12.10; standard library only.

Command:

```text
python -B -m unittest research.analysis.obligation_conservation_5817_t0_v1.test_t0 -v
```

Observed result: 5 tests passed. Coverage includes the exact 11-history replay/audit, overlap vs disjoint/unknown admission, transfer/timeout/parent-close conservation, separate compensation child and duplicate rejection, and five auditor-rejected mutations: dropped obligation, timeout relabeled as resolution, outstanding count decremented on transfer, missed alias overlap, and omitted compensation child.

The local candidate-to-auditor pipeline independently returned `PASS_METHOD_SCOPED` for 11 cases, 14 IDs and 0 errors. This is construction evidence, not an extra formal Docker invocation. Docker Desktop's local Linux engine pipe did not respond during the diagnostic window; allocation-02 therefore used the pinned, isolated GitHub-hosted Docker runner recorded in its run bundle.
