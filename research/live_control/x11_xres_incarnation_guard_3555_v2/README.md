# XRes alias-incarnation guard, OrbStack v2

Successor experiment for [issue #3662](https://github.com/Unjuno/agent-interface/issues/3662), preserving #3555/#3568 v1 evidence and #3575's pre-input STOP unchanged.

## Hypothesis and scope

On a private Linux/arm64 Xvfb server, a new client process can inherit the exact prior window XID, geometry, and pixels while having a different process PID and `/proc` start time. A guard that checks only the XID/visual alias should therefore refuse the stale p1 identity before bridge emission, while accepting a fresh p2 identity. XRes PID plus `/proc` start ticks are corroborating incarnation identifiers. This single OrbStack allocation is not a product/default-runtime claim.

## Evidence and status

`PRECHECKS.md` preserves construction failures and pre-input gates. `REPORT.md` records the single formal allocation and scope; raw event data, positive-control effect, and independent audit are in `artifacts/formal_01/`. Never overwrite predecessor v1 evidence.

## Reproduction

Build from the repository root with the pinned base image available locally:

```sh
docker build --network=default -f research/live_control/x11_xres_incarnation_guard_3555_v2/Dockerfile -t issue3662-xres-v2:formal .
```

Run only after source/image hashes, engine metadata, and output allocation are frozen. The formal container must use `--network none`, private Xvfb, read-only source, and a dedicated writable output directory. Mount this experiment directory at `/work/repo` and invoke `python3 /work/repo/src/formal_runner.py` once. Then run the frozen audit routine in a separate network-disabled container, with the freeze manifest hash bound to the raw result:

```sh
python3 -c 'import audit; raise SystemExit(audit.main("/work/out/raw.json", "/work/repo/FREEZE.json", "/work/out/audit.json"))'
```

Do not rerun a failed formal allocation; open a successor issue if the failure yields a testable correction. The auditor's CLI argument-count check is incorrect; the direct entry point above is the invocation used for this allocation.

The transition PASS concerns only stale-alias refusal before any bridge/native click and one fresh positive-control button effect with button release verified. It does not test arbitrary applications, remote X11, model/provider behavior, or broad desktop integration.
