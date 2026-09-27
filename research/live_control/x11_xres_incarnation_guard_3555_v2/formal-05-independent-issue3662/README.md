# XRes alias-incarnation guard, OrbStack v2

Successor experiment for [issue #3662](https://github.com/Unjuno/agent-interface/issues/3662), preserving #3555/#3568 v1 evidence and #3575's pre-input STOP unchanged.

## Hypothesis and scope

On a private Linux/arm64 Xvfb server, a new client process can inherit the exact prior window XID, geometry, and pixels while having a different process PID and `/proc` start time. A guard that checks only the XID/visual alias should therefore refuse the stale p1 identity before bridge emission, while accepting a fresh p2 identity. XRes PID plus `/proc` start ticks are corroborating incarnation identifiers. This single OrbStack allocation is not a product/default-runtime claim.

## Evidence and status

`PRECHECKS.md` preserves construction failures and pre-input gates. The formal raw result and independent audit are stored alongside it after the single allocation. Never overwrite predecessor v1 evidence.

## Reproduction

Build from the repository root with the pinned base image available locally:

```sh
docker build --network=default -f research/live_control/x11_xres_incarnation_guard_3555_v2/Dockerfile -t issue3662-xres-v2:formal .
```

Run only after source/image hashes, engine metadata, and output allocation are frozen. The formal container must use `--network none`, private Xvfb, read-only source, and a dedicated writable output directory. Start exactly one Xvfb and invoke `python3 /work/src/formal_runner.py` once. Then run `python3 /work/src/audit.py /work/out/raw.json` in a separate network-disabled container. Do not rerun a failed formal allocation; open a successor issue if the failure yields a testable correction.

The transition PASS concerns only stale-alias refusal before any bridge/native click and one fresh positive-control button effect with button release verified. It does not test arbitrary applications, remote X11, model/provider behavior, or broad desktop integration.
