# Immutable GTK source bundle audit (#2780)

This additive path repairs the source-integrity STOP recorded on #2606. It
audits the exact runner, GTK fixture, matrix gate, and runtime modules required
by the formal allocation before Docker is started.

The auditor is offline and fail-closed. It records SHA-256 values for every
discovered local module and returns PASS_SOURCE_BUNDLE_FREEZE only when every
required path exists and every local import resolves inside the same checkout.
A missing runtime tree therefore produces STOP_SOURCE_BUNDLE, rather than a
misleading case result.

This is a source-bundle contract, not a live GTK result and not #2606
acceptance. The one Docker allocation may start only after this audit passes;
the prior pre-case STOP and #2748 readiness PASS remain unchanged.

Run it from the repository root with:
python research/integration/golden_v3_second_domain_2246_v1/source_bundle_2780/audit_source_bundle.py --root . --manifest source-manifest.json
