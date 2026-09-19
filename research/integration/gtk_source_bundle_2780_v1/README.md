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

The transitive closure audit also walks `runtime.*` imports from the runner,
fixture, and scorer. The first closure allocation reached `runtime.backends`
but then stopped because the container lacked Python Xlib. `Dockerfile`
defines the local successor image, based on the immutable #2748 image and
adding Debian `python3-xlib`; local image digest:
`sha256:8e249b9ab9761d1c14fada1eca727b55564f70d67b0f06ae9e9854682fd60199`.
