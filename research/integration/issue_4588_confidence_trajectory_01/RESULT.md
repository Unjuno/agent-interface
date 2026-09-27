# Issue #4588 — confidence-trajectory construction result

Allocation: `issue-4588-trajectory-20260927-01`. Source was frozen on the Issue before formal invocation at commit `9fe6e89141805e3a7b29d4adc08d9043e2a664c2` (base main `92596bfb750be63c03d3d2906a05d5a5933651c2`), path `research/analysis/confidence_trajectory_construction_v1/`.

## H / T / D / C / U

**H.** Confidence trajectories may distinguish decisions hidden by a single current level; curvature may add information after level plus velocity but amplify confidence measurement noise. A fixed causal smoother may lower this noise, while lag remains unmeasured.

**T.** One OrbStack Docker invocation, Python 3.12.14 / `linux/amd64` (`x86_64`), `--network none`, container read-only, source mount read-only, fresh result directory, standard library only. The frozen corpus has 35 three-sample traces and 17 transition families, including every family enumerated in Issue #4588. The noise study exhaustively enumerates 27 triples from `{-0.01, 0, +0.01}` around a constant signal.

Exact command:

```sh
docker run --rm --platform linux/amd64 --pull=never --network none --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=32m \
  -v /tmp/issue4588-v1/src:/src:ro \
  -v /tmp/issue4588-v1/evidence:/out:rw \
  -w /src -e PYTHONPYCACHEPREFIX=/tmp/pycache python:3.12-slim \
  python experiment.py --out /out/FORMAL_RESULT.json --source-dir /src
```

**D.** `PASS_CONSTRUCTION_INFORMATION_AND_NOISE_BOUNDARY`.

- Four of four equal-current-level groups contain three distinct labels (`ACTION`, `YIELD`, `NO_OP`): current level alone cannot identify the authored correct class in those groups.
- Four of four second-order alias pairs have equal current level and velocity but different labels; acceleration separates all four.
- All three stale, epoch-mismatched or missing-history cases emit `YIELD` in the contract fixture. `NO_OP` and `YIELD` are distinct labels.
- On the bounded 27-point grid, velocity noise RMS = `0.0115470054`, raw acceleration noise RMS = `0.0200000000`, and causal-smoothed acceleration noise RMS = `0.0066666667`.
- Independent raw auditor: PASS, errors `[]`, all 35 rows reconstructed. Formal invocations 1; reruns/replacements/tuning 0.

**C.** The trajectories and labels are authored fixtures. This tests representational aliasing and a bounded noise transformation, not a learned System-1 policy, realistic event frequency, calibrated confidence or deployed false-action rate. The smoother's signal lag is not evaluated. No GUI, model, input, runtime authority or user data was used.

**U.** Whether a fitted controller improves held-out decision accuracy, false-executable rate, NO_OP stall risk, or task outcome under realistic confidence calibration/noise/timing remains unknown. No cost/latency or cross-application result is established. This PASS justifies a preregistered held-out, model-capacity-controlled, authority-neutral policy experiment; it does not authorize live actions.

## Raw hashes (SHA-256)

- `FORMAL_RESULT.json`: `34c93f1742962ca1bbef9e115bb7456703f263b4ff1ac442cced584d4213bdee`
- `INDEPENDENT_AUDIT.json`: `bfa0b659e31150bd8754b19345b4db78dde7dee668d4d0d659e51bbcf262d7e4`

Source manifest and exact frozen inputs are retained in the analysis path above. No source or decision gate was edited after freeze.
