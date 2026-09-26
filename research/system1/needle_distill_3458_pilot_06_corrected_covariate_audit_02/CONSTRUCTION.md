# Construction and freeze record

Issue #3899 formal allocation `needle-3869-covariate-audit-corrected-02`.

Before formal audit, a local `needle-pilot05:local` Docker construction run executed 6/6 unit tests (0.022 s) and the dedicated corruption self-test (6/6 feature columns rejected). It did not read the formal result, train a model, or invoke the model runner. The suite-specific velocity/confidence test confirms those values can differ across the IID and shifted generators while a row is still compared exactly to its own regenerated expected values. A non-fatal PyTorch warning noted NumPy is not installed; no NumPy-dependent operation is used.

The frozen input is the already-retained #3869 result; the corrected auditor makes no training/inference call. Freeze code, tests, preregistration, environment, and input identities are recorded in `FREEZE.json`. Exactly one subsequent formal Docker invocation is allowed; no retry.
