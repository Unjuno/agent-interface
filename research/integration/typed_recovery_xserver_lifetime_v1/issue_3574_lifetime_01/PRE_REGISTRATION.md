# Issue #3574 — allocation issue3574-lifetime-01

This is an additive evidence-completeness successor to #902/#3555. Preserve the earlier 8-row comment, audited XRes alias outcome, initial auditor STOPs, and missing-provenance disclosures without modification.

## Frozen source and environment

- Source base: main `61311817969251b814cb00b568a75c91a3591d3e`.
- Exact unchanged #881 validator: `research/integration/integrated_recovery_epistemic_surface_key_v1/src/validator.py`; Git blob SHA-1 `91983ab78a06b93cc7fdd829b6094fd255f18210`. The frozen local copy was byte-compared with this GitHub source and its Git blob SHA recomputed.
- Container: `agent-interface-3548-routes:20260920`, immutable `sha256:76af6aaaab4419b3f799f3121aab191a347130cad07080ac285e3b6d9896cefc`, `linux/arm64`.
- Freeze manifest SHA-256: `b216042ce7ad3194b44ac25368c6143b4900e6400e6a7fa0b4ef7c641e7bea60`.
- Runner SHA-256: `391bde40f91483a1bcf5956ba2e8a986ae4666b49331267521173c9e56a538f7`.
- Independent auditor SHA-256: `f2e53076aeecf2ac2570afb8aafc6673caaab2bbf62905b11065793c5922a503`.
- Frozen validator SHA-256: `014b6fc6e47253eaa2a019e425c9bce4dbb7375f1ac653f98c9af10175b042c3`.

The runner independently checks these frozen hashes before opening Xvfb. The raw report binds the freeze-manifest SHA, source commit and image identity. The auditor independently checks source/manifest hashes and reconstructs results without importing runner, Xlib, or the candidate validator.

## Formal command and decision

One container invocation only, with network none, read-only `/freeze`, and fresh writable `/evidence`:

```sh
docker run --rm --network none --platform linux/arm64 \
  --env PATH=/opt/transport-venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
  --mount type=bind,src="$PWD/freeze",dst=/freeze,readonly \
  --mount type=bind,src="$PWD/evidence",dst=/evidence \
  agent-interface-3548-routes:20260920 python3 -B /freeze/lifetime_runner.py
```

The exact runner creates four G1/G2 pairs on Xvfb `:149`, always with one newly recreated first Xlib fixture client per server. It makes no controller/input calls. Each pair yields four frozen classification rows. The only PASS is `PASS_XSERVER_LIFETIME_BINDING_REQUIRED_SCOPED` after all four XID/pixel/typed-identity reincarnations, all 16 policy rows, negative controls, process/socket cleanup, manifest checks, raw-only independent audit, and corruption controls pass. No rerun/tuning or production change is in scope.
