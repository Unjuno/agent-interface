# Issue #3642 — GTK effect binding result

Decision: **PASS_TK_EVENT_WITNESS_AND_PUBLIC_MCP_CONTINUATION_SCOPED**.

One pre-registered Linux/arm64 OrbStack allocation (`issue3642-gtk-effect-01`)
matched the guarded candidate and independent prefix oracle on all five events.
Only the two admitted `emit` deltas were translated to XTest Space press/release.
The GTK counter/title progressed 0→1 on gen-1, stayed at 1 through replacement,
delayed old replacement, and old-generation observation, then progressed 1→2 on
the valid gen-2 observation. Both physical key states were verified empty.
Fixture and Xvfb exited 0 and were reaped; the X11 socket was removed.

The independent raw-only audit ran in a separate pinned OrbStack container:
33 checks, zero failures. The frame SHA256 sequence (initial then five prefixes)
was:

```text
03a682f689fcbcf1cae80e321226ccbeedb4191ff5f670a42cb8e43e3321395b
c4103cad0e0671111693e6218e348d5ec95f9874bc34935f1f867cdbe2b24e95
c4103cad0e0671111693e6218e348d5ec95f9874bc34935f1f867cdbe2b24e95
c4103cad0e0671111693e6218e348d5ec95f9874bc34935f1f867cdbe2b24e95
c4103cad0e0671111693e6218e348d5ec95f9874bc34935f1f867cdbe2b24e95
d63c608e8098b4134e6e2fbfdee5d17b90c84f74123872ddcb97f0d79e4cbf92
```

This is one synthetic GTK/X11 policy-to-effect result only. It does not establish
production runtime safety, real event-source ordering, model/MCP use, general
application correctness, latency/cost, or human benefit. Earlier #3518/#3588
evidence and excluded exploratory smoke runs are not modified or promoted.

## Evidence

- `PREREGISTRATION.md`, `FREEZE.json`: frozen H/T/D/C/U, source hashes, and
  invocation before formal allocation.
- `evidence/allocation.json`: event-prefix actions/states, visible effects,
  releases, process identity/lifecycle, and log hashes.
- `evidence/frame-00.raw` through `frame-05.raw`: exact XGetImage bytes.
- `evidence/fixture.log`, `evidence/xvfb.log`: retained process logs.
- `evidence/audit/AUDIT.json`: independent raw-only 33-check result.
- `evidence/SHA256SUMS`: checksums for every raw allocation and audit file.

## Reproduction

Use the exact one-allocation and one-audit commands frozen in
`PREREGISTRATION.md`. Formal collection is not to be repeated; the committed
outputs are the result for this allocation ID.
