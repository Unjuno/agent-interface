# Source freeze capsule — Issue #4190

This is the exact preformal source/gate capsule. Formal invocations were 0 when these bytes were created.

Decode `SOURCE_FREEZE.tar.xz.b64`, verify archive SHA-256 `15e5e22a3972db6bb47a41e513dbf74a26579d7f5f504a8bc9b86874e25ec1da`, then extract. The capsule contains candidate/runner/auditor, construction evidence, FREEZE.json, and exact vendored upstream sources.

Construction was excluded: 10/10 cells, audit errors=[], candidate complete 5/5, unsafe lifetime failures 2/2, corruption controls 10/10 rejected. No source correction followed construction.

No Docker/OrbStack image identity is claimed; actual environment is recorded in the capsule.
