# Issue #59 — retained v39 fire-cover ammo timeline (posthoc)

**Disposition: `NO_ZERO_EXPOSURE`; full-result reconstruction audit `PASS`.**

The original `audit.py` and `AUDIT.json` remain unchanged as historical v1 artifacts. A mutation review showed v1 could return `PASS` after reported fields were altered. The first v2 repair reconstructed the window rows and several totals, but its checks did not enforce exact JSON types consistently, and an audit failure still exited successfully. This hardened v2 reconstructs and compares the entire result object against raw data from the frozen Git blobs, with exact type checks and a nonzero exit on mismatch.

`AUDIT_V2_FREEZE.json` pins the P01 package artifacts at commit `ec71c53411055b1d3960ca7c947b52a70c5dca2f` and embeds the original P01 source freeze. `AUDIT_V2.json` is the generated result. `test_audit_v2.py` covers the unchanged result, eight summary mutations, bool/int aliasing, and reproduces the legacy false-PASS.

This is audit-integrity work only. The retained trace still has three active fire-cover windows, seven observed ammo decreases, no zero-ammo exposure, and no time-local useful-effect events. It adds no new game trace, gameplay allocation, controller behavior, or causal evidence. Issue #59's live v39 control and useful-effect requirements remain open.

## Reproduce

From repository root:

```sh
python3 -B -m unittest research.doom.v39_fire_cover_ammo_timeline_59_p01_20261005.test_audit_v2 -v
python3 -B research/doom/v39_fire_cover_ammo_timeline_59_p01_20261005/audit_v2.py
```

The audit requires the pinned Git objects to be available locally and does not rewrite the raw predecessor.
