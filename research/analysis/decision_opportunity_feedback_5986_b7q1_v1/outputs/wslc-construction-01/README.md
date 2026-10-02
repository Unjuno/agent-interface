# WSLc construction compatibility check

This is a **construction-only compatibility check** of the already-frozen Issue #5986 `test_construction.py`. It is not a second candidate or auditor execution and does not amend the original `DECISION-OPPORTUNITY-5986-T0-20261002-01` outcome.

## Result

- Suite: 8/8 tests passed, exit 0, reported runtime 0.001 s.
- Formal candidate invocations: 0. Formal auditor invocations: 0. Retries: 0.
- Runtime: WSLc 3.0.1.0 via `wslc.exe` 5.0.1.1; cached `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`; Python 3.12.14, linux/amd64.
- Network disabled, one CPU requested, 512M requested, GPU/model/audio/GUI/host input disabled.
- The WSLc invocation emitted: “Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.” Memory-limit enforcement is unknown; this does not establish memory-pressure relief or a memory benefit.

This establishes only that the frozen standard-library construction suite runs in the cached WSLc Python image. It does not validate the formal candidate/auditor inside WSLc, empirical feedback value, a production route, or WSLc-versus-Docker performance.

## Exact command boundary

The package was mounted read-only at `/src`; this new output folder was mounted separately at `/out`. The inline driver ran:

The output bind was nested under the package's host directory, so inside this one-off harness `/out` was a writable submount beneath the otherwise read-only `/src` tree. The frozen test suite did not write source files. This layout is recorded as-run, not recommended as a formal candidate/auditor mount pattern; a future formal run should place output outside the source tree.

```text
python -c <inline wrapper invoking /usr/local/bin/python -B -m unittest -v test_construction.py>
```

Outer WSLc command:

```text
wslc container run --rm --pull never --network none --cpus 1 --memory 512M --name ai-5986-wslc-construction-20261002 --mount type=bind,source=<decision_opportunity_feedback_5986_b7q1_v1>,target=/src,readonly --mount type=bind,source=<outputs/wslc-construction-01>,target=/out --env PYTHONDONTWRITEBYTECODE=1 --workdir /src python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f python -c <inline wrapper>
```

`RUN.json` records the exact inner argv, WSLc-observed source byte hashes, stdout/stderr hashes and formal invocation counts. The source commit used was `f6c6d2004bf57971e97fe889ab8e50d10a3b5ed7`.
