# Issue #3631 formal-04 report

## Formal disposition

`PASS_PROXY_BINDING_EFFECT_UNIT` for this frozen synthetic fixture allocation only.

- Allocation `issue3631-proxy-effect-unit-formal-04`; exactly one runner invocation, 28/28 unique rows, zero runner errors, zero retries.
- Each of four representation arms produced one exact counter 0→1 positive effect. Each also yielded/refused for the six preregistered controls: acknowledgement-only/no effect, stale version, replaced process incarnation, unavailable target, two-target ambiguity, and macro failure.
- XRes LocalClientPID and stable `/proc` start ticks bound each selected XID to the fixture process incarnation. Screenshot, proxy image, structured control rect, and hybrid each recorded their input hashes and derived coordinates.
- Ambiguous controls observed two ready processes and distinct XIDs before admission; zero input acknowledgements/effects occurred. All 28 root-window Button1 observations were released; all child processes were reaped and Xvfb sockets disappeared.
- Independent read-only-container audit: `PASS_INDEPENDENT_AUDIT`, zero errors. All seven corruption challenges were detected: missing row, forged XRes owner, forged derived coordinate, wrong output path, stale admission, removed ambiguity, and pressed release.
- OrbStack/Docker pinned image: `sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27`, `linux/arm64`; formal network disabled, root filesystem and source read-only.

## Retained hashes

- Raw JSON SHA-256: `048bf3730a73c9dde59ea13db4f036b46a6f10acc27ac01c86e19207044bdec7`.
- Independent audit JSON SHA-256: `dfaaeb8b9412c4691177edc7c8525e65b59f753a723cf8aa1e28fed5f8f2564e`.
- Post-formal cross-binding audit SHA-256: `45880c0c945603572752f90ea796245f2414eebee41b18f02a93844de8523706` (`PASS_SUPPLEMENTAL_CROSS_BINDING_AUDIT`, 28/28 rows; current dispatch state, screenshot/proxy/structured/hybrid bytes, state identity, derived coordinate and payload lengths independently recomputed).
- Runner self-hash: `b240cb00076a75bdc2de1049ca55684dd9480adf72b7a30813f090fe4bcd720d`.
- Construction evidence is in `evidence/preflight-04/`; the raw rows and audit are in `evidence/formal-04/`.

The supplemental audit was authored after the formal run and does not alter or rerun the frozen allocation. It independently cross-checks action-state continuity for positive/no-effect cases and representation-specific state/coordinate binding beyond the frozen primary auditor's seven corruption probes.

## Scope and uncertainty

This establishes only a deterministic GTK/Xvfb effect-binding and safety-gate result. It does not compare model or human usability, latency, cost, or representation quality; it does not establish general GUI safety, production authority, or integrated desktop success. No arm winner or benefit claim is made. Preserve this allocation and predecessor #3619/#3626 results unchanged.
