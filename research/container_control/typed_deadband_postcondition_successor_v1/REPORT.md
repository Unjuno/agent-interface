# Typed deadband/postcondition successor v1 — report

Status: PASS_CONTAINER_X11_MECHANICS_SCOPED

Issue: #2017
Fresh execution identity: `TYPED-DEADBAND-POSTCONDITION-SUCCESSOR-V1-001`
Workflow run: 35442976600
Artifact: typed-deadband-successor-v1-35442976600
Artifact ID: 10584084448
Artifact digest: sha256:e8a010df6c5a3a20e06590c244b2f4cec8c6b14ab592d36c177a9ddb1be09a35
Source commit in manifest: `8e3fcb75656e9bf28f2b6270ecd8d82496d1ea30`

## Execution

The isolated Ubuntu 24.04 Actions runner installed Xvfb, Tk and python-xlib, then ran the frozen successor runner once with:

- pairs: 3
- decisions per arm: 6
- planner wait: 0.34 s
- cover budget: 0.24 s
- typed deadband: 0.06 normalized units

The historical v1 construction stops remain preserved in `STOP_HARNESS_SYNTAX_ERROR.md`. This is a fresh execution identity; no failed run was rerun.

## Result

All three matched coast/recovery pairs improved the preregistered unsafe-time metric:

| pair | coast unsafe ms | recovery unsafe ms | recovery − coast ms |
|---:|---:|---:|---:|
| 0 | 485.946 | 355.940 | -130.006 |
| 1 | 662.436 | 371.979 | -290.457 |
| 2 | 664.058 | 356.182 | -307.876 |

Median recovery-minus-coast unsafe time: **-290.457 ms**.

Recovery center-region time was 1181.716, 1067.744 and 1230.917 ms for the three pairs. These are fixture descriptors, not a human-tempo measure.

## Safety and audit gates

- formal mechanics pass: true;
- terminal input empty: 12/12 arms;
- app-side key events balanced: 12/12 arms;
- stale repress before planner return: 0;
- guard invalidation events: 5;
- maximum guard-to-app release: 0.281113 ms;
- maximum posthoc visual decoder error: 0.018083;
- decision count: 6/6 for every arm;
- artifact manifest SHA-256 mismatches: 0.

Guard events reached observed positions 0.0412–0.0588, below the 0.06 typed threshold, providing the required task-relative cancellation exposure. The run also exposed natural stale-guard invalidation.

## Disposition and limits

This is a **scoped PASS for the rendered Tk/X11 mechanics fixture only**. It supports the claim that the typed threshold can cancel the bounded recovery path while retaining the declared release and stale-authority gates in this finite allocation.

It does not establish DOOM efficacy, GUI generality, human operating tempo, model quality, token savings, latency improvement, production safety, or a universal safety guarantee. The artifact is retained for 30 days by Actions and is referenced by its immutable run ID and digest. The raw evidence remains in the artifact; historical reports are unchanged.

Next gate: independent transfer outside this synthetic fixture before any broader promotion.