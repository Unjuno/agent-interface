# Formal result: XRes alias-incarnation guard, OrbStack v2

Issue: [#3662](https://github.com/Unjuno/agent-interface/issues/3662), successor to #3575. Allocation: `issue3555-xres-guard-orbstack-v2-formal-01`.

## H/T/D/C/U

- **H:** A stale window alias with reused XID, equal geometry, and equal pixels is rejected when its process PID/start ticks differ; a fresh incarnation is admitted and can produce one controlled effect.
- **T:** Freeze source, fixture, audit, image, platform, XRes/Xvfb versions, network and mounts; perform one private OrbStack allocation with a stale refusal before bridge emission and then a fresh positive control.
- **D:** Scoped PASS requires equal XID/geometry/pixels, distinct PID/start ticks, matching XRes PIDs, zero stale emissions/effect, one fresh-control emission/effect, release, cleanup, independent audit and corruption challenges.
- **C:** One Linux/arm64 OrbStack container with private Xvfb; no external network, remote X11, model/provider, default-runtime or production inference.
- **U:** Whether this observed guard behavior generalizes beyond the fixture/private-Xvfb environment remains unknown.

## Result

`PASS_SCOPED_STALE_REFUSAL_AND_FRESH_CONTROL` in the one frozen formal allocation. p1 and p2 reused XID `2097167`, had equal geometry `[80,80,240,160,24]` and equal pixel SHA-256 `871bca1ba588f1ea184ea311181c785fc1843ac577a13427c74ee70647db3fb2`. PID changed `21 -> 25`; `/proc` start ticks changed `312992 -> 313057`; XRes 1.2 reported the matching PID for each incarnation.

The stale alias was refused before bridge call: `bridge_called=false`, emissions `0`, no effect file. The fresh p2 identity was admitted; one xdotool click caused exactly one fixture effect by PID 25, and Button1 was observed released afterward. Final bridge emission count was one. Formal runner completed and the `--rm` container exited; its Xvfb was terminated by the cleanup trap. The Xvfb log is empty.

The independent offline auditor returned `PASS_INDEPENDENT_AUDIT`, zero errors, and rejected three corrupted copies: changed XID, stale admission, and hidden fresh emission. Its initial CLI invocation had a usage error; the frozen audit function was then invoked directly in a distinct network-disabled container. This did not rerun the formal allocation or alter raw data.

## Evidence

- Freeze manifest SHA-256: `f40494b1be99fb1e68d7b09c498297df35a72c043740b5f09d3faec7e059acfe`
- Raw result SHA-256: `ccb9a75eefb7df73cb13dbc9191d33334fb672c2fd58fcc5fa32be998e182807`
- Independent audit SHA-256: `fdce1b10b7c46381d41d1e0151476b548658de0354bd4ef3db0af3d33200e4dc`
- Positive effect SHA-256: `49a31539c166b8200d894fa1b7b52b7cff9699d953142cc41cd8f45fba7b7dd9`
- Frozen source commit: `fe69162290557a56b52678c782f5b763001df196`
- Formal image: `sha256:6efffbdf1526d51a1e4c7076b41ce021454986ac5fc5ef6ed971aca1e445ee0d` (`linux/arm64`), from the pinned base in `FREEZE.json`.

## Limits

This verifies only the frozen identity-guard transition and fixture effect under one private OrbStack Xvfb allocation. It does not establish general application integration, protection against all X11 lifecycle races, cross-host behavior, or product/default policy. Integration work should independently reproduce before promotion.
