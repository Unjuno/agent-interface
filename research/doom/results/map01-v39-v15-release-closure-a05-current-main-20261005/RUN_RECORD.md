# A05 run record

Classification: static Git-object provenance audit; not candidate execution, a formal allocation, or live computer-control evidence.

Source: `origin/main` at `b5be19963454ce5edafc945b78b100012952dd15`.

Commands (repository root):

1. `python -B research/doom/results/map01-v39-v15-release-closure-a05-current-main-20261005/derive_current_closure.py`
2. `python -B research/doom/results/map01-v39-v15-release-closure-a05-current-main-20261005/audit_current_closure.py`
3. `python -B -m py_compile research/doom/results/map01-v39-v15-release-closure-a05-current-main-20261005/derive_current_closure.py research/doom/results/map01-v39-v15-release-closure-a05-current-main-20261005/audit_current_closure.py`

Outcome: builder and independent auditor emit `PASS_STATIC_IMPORT_CLOSURE`; 38 source files, zero unresolved configured-local imports, external roots `PIL,Xlib,numpy,vizdoom`. Source blob/content hashes match 38/38. A04-to-A05 comparison: 0 changed, 0 added, 0 removed blobs.

Negative controls: changing the expected main SHA to an incorrect value is rejected by the pinned-head assertion; changing a manifest source SHA-256 is rejected by the independent verifier. Both controls were applied to temporary copies of the manifest and restored before package hashing.

No candidate/production module was imported or executed; no container, display/game, model, or input was used. No formal allocation was consumed.
