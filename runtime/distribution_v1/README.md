# Standalone doctor distribution v1

Build a deterministic external-dependency-free bootstrap artifact:

```bash
python -m runtime.distribution_v1.build \
  --out dist/agent-interface-doctor.pyz \
  --manifest dist/MANIFEST.json \
  --sums dist/SHA256SUMS
python dist/agent-interface-doctor.pyz
```

The artifact contains only the promoted OS-neutral core and native discovery
doctor. It does not bundle or activate native effect backends and always reports
`ready_for_side_effects=false`.
