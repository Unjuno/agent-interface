# XRes process-incarnation guard for recycled XID aliases (allocation 02)

**Observed gate:** `PASS_GENERATION_GUARD_REJECTED_STALE_ALIAS`  
**Independent raw-only audit:** `PASS_INDEPENDENT_RAW_RECONSTRUCTION` (8/8 corruption controls)  
**Preregistration provenance:** `INCOMPLETE — original freeze and source-manifest bytes were not retained`

This is one research-wrapper result against the pinned `NativeHandleBridge`, linux/arm64 container and private Xvfb fixture. It is not a production/default-runtime security claim or a result for remote X11 servers.

## Hypothesis and method

Bind a visual alias to the X-Resource server-reported `LocalClientPID` plus contemporaneous `/proc` process start ticks, then recheck that process incarnation before native input. A stale alias after XID recycling should refuse before `bridge.click`, with no backend emissions or p2 effect; a fresh p2 alias should remain usable.

The allocation followed the H/T/D/C/U recorded on Issue #3555, with a private Xvfb display, network disabled, read-only source mounts, one formal runner invocation and no retries. The stale-alias failure path stopped immediately after recording its result; the fresh positive control was conditional on safe stale refusal. The raw records freeze/source-manifest SHA-256 values, but the exact original files matching those values were not retained. Later edited versions exist and are explicitly not substituted for the originals. Thus the observation and independent raw reconstruction are reproducible from the retained raw, but byte-level preregistration verification is incomplete.

## Observed result

- XRes negotiated 1.2. p1 was PID 14/start ticks 5208475; p2 was PID 17/start ticks 5208479.
- Both fixture clients used XID 2097152, geometry `[80,80,240,160]`, and equal 153600-byte client-window buffers with SHA-256 `3b80132900d7ab9ce6a54b7f01b7fa0d345dd50aafb69135b740ae655c3aba0c`.
- The old p1 alias was refused as `PROCESS_INCARNATION_MISMATCH`. `bridge.click` was not entered; backend emissions remained 0; the independent p2 effect stayed `[0,0,0]`.
- The fresh p2 alias was permitted and completed; backend emissions increased by 3; the independent effect became `[1,212,118]`.
- The fresh control's release receipt was verified with empty keys/buttons. Bridge closed and both fixture processes exited with code 0.

## Audit and provenance

The initial candidate auditor stopped because its corruption-control expectation was incorrect. That STOP is retained in Issue #3555 and is not hidden. A separate raw-only auditor, importing none of the candidate guard, bridge, runner, or fixture, then reconstructed the result from the immutable raw record and passed all eight corruption controls. It also verified all six PNG files against their recorded sizes and hashes. This does not repair the missing original freeze/source-manifest files or upgrade the result to a fully provenance-verified PASS.

- Allocation: `issue3555-xres-guard-formal-02`
- Tested source commit: `49535d91424c3786330ec62e6d621e4e1eaf1c49`
- Container image: `sha256:e47cbddc70722a816758a4a1c27cf2a38071c889670be98bf3eacdc9fff17916`
- Raw SHA-256: `39aee2c0614a411aefe602b9d9e7ae910b9aa5cc59796b209ca176909acd101d`
- Freeze SHA-256 embedded in raw: `4100c858b729e970a701808fcf9964ae1131efe3ccc8bf0c58db5369b546eb74`
- Source-manifest SHA-256 embedded in raw: `7af1514fea3ec5746bcf5d7aae9d72debaf996810a7d8a9ec01451ef2c68e177`
- Independent auditor SHA-256: `94178c3457b21a4640eecabefdbef99dc2e05b9c8bce5c1f39af1740c9ef53f1`
- Independent audit JSON SHA-256: `0a357fff35820b5f09ffd826f440df47a75f402c0c154d5690708b94d3cd3f44`
- Consolidated final audit SHA-256: `b34486bb2a8aa3a4be468deef42dec7827c5495b0b8ca14b7e73358b3b01cf33`

## Limits and next question

This only establishes that the tested XRes PID plus `/proc` start-ticks comparison distinguished and rejected the recycled-XID alias in this one pinned local fixture allocation. It does not establish resistance to all X11 races, remote transports, other X servers, other processes, production compositor behavior, or correctness of an unmodified runtime. The candidate remains research-only; promotion would require separately reviewed integration and broader evidence.

Next analytical step: inspect the native click call path for a time-of-check/time-of-use window between owner revalidation and actual event emission. Only if that call path offers an enforceable atomic boundary should a separate successor test the adversarial owner-switch race.
