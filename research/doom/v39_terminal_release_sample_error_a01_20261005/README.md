# V39 owner cleanup when keymap sampling fails

## H / T / D / C / U

**H.** On the current-main V39 owner path, terminal cleanup sends the touched-key UP before querying server key state. If that query fails, cleanup should preserve an explicit unverified receipt, identify the key as unknown, and keep the owner available for a bounded retry rather than losing the owner-release record.

**T.** One CPU-only WSLc construction run uses the exact current-main `input_owner_v12.py` through its V3/V4 transition wrappers and a fake X server. The fake server accepts one KeyPress, accepts the cleanup KeyRelease, then throws exactly once from `query_keymap`; the candidate checks the failure receipt and performs one bounded cleanup retry with sampling restored. A separate raw-only auditor recomputes event ordering, receipt state, and mutation controls. No model, game, GUI, real X server, OS input, GPU, or live allocation is used.

**D.** `PASS_SYNTHETIC_CLEANUP_SAMPLE_FAILURE` only if KeyRelease precedes the injected failed sample, the exception carries the retained `owner_release` receipt, the receipt is unverified with the touched key listed as unknown and a typed sample error, and a later cleanup pass samples empty state and verifies release. The independent audit must also reject every frozen mutation.

**C.** A fake display deterministically applies KeyRelease to an in-memory set; it cannot represent real X server behavior, shared-display races, physical keys, or application consumption. The exception is injected after XSync and does not model transport loss.

**U.** This is one source/construction result for query failure during terminal cleanup. It does not establish physical release, real-X behavior, useful feedback, latency bounds, recovery efficacy under gameplay, threat response, task success, or MAP01 completion. Issue #59's separately gated live-game threat exposure remains open and unassigned.

## Reproduction

The freeze pins the source commit, copied source/test hashes, image digest, commands, and decision gates. The container mounts only this additive package read-only plus a separate writable output directory. The candidate emits one raw JSON event trace; the independent auditor reads only that trace and the saved candidate output.

```powershell
wslc.exe run --rm --pull never --network none --cpus 1 --memory 512M --mount type=bind,source=<package-directory>,target=/src,readonly --mount type=bind,source=<allocation-output>,target=/out python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016 python -B /src/candidate.py
wslc.exe run --rm --pull never --network none --cpus 1 --memory 512M --mount type=bind,source=<package-directory>,target=/src,readonly --mount type=bind,source=<allocation-output>,target=/out python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016 python -B /src/audit.py /out
```

Each frozen invocation runs once. Preserve any first failure or STOP without retry. WSLc's configured resource limits are not treated as proof of enforcement.

The host-Python construction harness was run once before the freeze and passed its candidate assertions plus all six raw mutations. Its setup output is retained separately under `outputs/v39-terminal-release-sample-error-a01-construction/`; it is not part of the WSLc result.
