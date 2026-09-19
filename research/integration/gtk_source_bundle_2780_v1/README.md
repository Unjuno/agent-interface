# Immutable source bundle for formal GTK matrix (#2780)

This additive path closes the source-integrity gap recorded in #2606 and
#2780. The formal runner, GTK fixture, matrix scorer, and imported runtime
modules are resolved from one sparse checkout before any Docker allocation.

Run `audit_bundle.py` from the repository root. It checks the exact runner,
fixture, scorer, and imported runtime module tree, then emits reproducible
SHA-256 digests. A formal allocation is permitted only after this audit passes
and its output is retained with the container image digest and source commit.

This is a freeze gate only; it does not claim GTK effect correctness or formal
#2606 acceptance.
