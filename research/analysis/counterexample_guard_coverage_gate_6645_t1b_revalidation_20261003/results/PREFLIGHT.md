# WSLc construction preflight

Before the frozen label probe, WSLc 3.0.1.0 ran the cached Python 3.12.14 image by digest with `--pull never`, `--network none`, one CPU, a requested 128 MiB memory setting, UID/GID 65534:65534, and the T1b candidate input directory mounted read-only. JSON fixture loading succeeded. WSLc warned that swap-limit capabilities are unsupported or cgroup is not mounted; memory enforcement is not inferred.

The final pre-candidate check also verifies this package's distinct writable output mount. These preflights are construction evidence only and do not invoke the candidate or auditor.

## Retained invocations

These two commands ran before the latest #5085 HOLD was noticed. Both used `--rm`, `--pull never`, and `--network none`; both exited 0 and emitted the WSLc cgroup/swap warning above. They establish only that the specific reads/writes below worked. They do not establish that the commands had no shared WSLc bridge effect; no post-HOLD WSLc inspection or invocation was made.

1. Read-only input/Python preflight (candidate invocations: 0):

```powershell
wslc run --rm --pull never --network none --cpus 1 --memory 128M --user 65534:65534 --mount "type=bind,source=C:\Users\junny\Documents\Codex\2026-10-03\agent-interface-6645-t1b-revalidation-lf\research\analysis\counterexample_guard_coverage_gate_6645_t1b_v1\candidate_input,target=/work,readonly" --workdir /work python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f python -B -c "import json,pathlib,sys; p=pathlib.Path('/work/candidate_fixture.json'); json.loads(p.read_text()); print('WSLC_PREFLIGHT_OK',sys.version.split()[0],p.stat().st_size)"
```

Output: `WSLC_PREFLIGHT_OK 3.12.14 1342`; exit 0.

2. Read-only repository plus separate writable-output preflight (candidate invocations: 0):

```powershell
wslc run --rm --pull never --network none --cpus 1 --memory 128M --user 65534:65534 --mount "type=bind,source=C:\Users\junny\Documents\Codex\2026-10-03\agent-interface-6645-t1b-revalidation-lf,target=/work,readonly" --mount "type=bind,source=C:\Users\junny\Documents\Codex\2026-10-03\agent-interface-6645-t1b-revalidation-lf\research\analysis\counterexample_guard_coverage_gate_6645_t1b_revalidation_20261003\results,target=/output" -e T1B_REVALIDATION_OUTPUT_DIR=/output --workdir /work python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f python -B -c "import json,pathlib; p=pathlib.Path('/work/research/analysis/counterexample_guard_coverage_gate_6645_t1b_v1/candidate_input/candidate_fixture.json'); json.loads(p.read_text()); pathlib.Path('/output/preflight_marker.txt').write_text('WSLC_OUTPUT_PREFLIGHT_OK\\n',encoding='utf-8'); print('WSLC_RW_OUTPUT_PREFLIGHT_OK')"
```

Output: `WSLC_RW_OUTPUT_PREFLIGHT_OK`; exit 0. It created [`preflight_marker.txt`](preflight_marker.txt), which is preserved. The frozen WSLc candidate and WSLc auditor invocation counts remain 0 pending #5085 reconciliation/explicit direction; native Windows construction-test candidate invocations are recorded separately in [`CONSTRUCTION.md`](../CONSTRUCTION.md).
