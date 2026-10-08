# MAP01 task-effect contract successor (Issue #2241)

This additive successor integrates the offline contract from PR #2217 onto current `main` without changing PR #2217 or its evidence. It addresses the review findings preserved there:

- task effects must use the same explicit `clock_domain` as the physical actuation;
- malformed task-effect timestamps are rejected before comparison.

The result is only an offline classifier/oracle check. It allocates no MAP01 task effect, live GUI/X11 input, model, network, or authority. A passing check does not establish live task success or desktop integration.

Reproduction:

```
python -m py_compile contract.py test_contract.py
python test_contract.py
```
