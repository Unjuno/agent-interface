# T0 formal invocation record

- Issue: [#7487](https://github.com/Unjuno/agent-interface/issues/7487)
- Allocation: `DELAYED-GUI-EFFECT-ATTRIBUTION-7487-T0-HOST-01-20261004`
- Preregistration comment: https://github.com/Unjuno/agent-interface/issues/7487#issuecomment-5977313414
- Frozen source commit: `13912c17ace3a5e33c4518a02d920e2a9ad1a3ad`
- Base main / merge-base at invocation: `94a7073617abe14f220d0a840ce4404f1bc299eb`
- Formal invocation time: 2026-10-04 06:28 UTC (system clock)
- Host: macOS 27.0.1, Darwin arm64 (`T6000`); Python 3.14.5
- Runtime: host-only standard library; **not container-isolated**
- OrbStack preflight: `docker context show` returned `orbstack`. One read-only `docker image ls --format '{{.Repository}}:{{.Tag}} {{.ID}}'` returned `Error response from daemon: rpc error: code = Unknown desc = blob sha256:68ca3975c1576d18f8cf52bcb6e153ce31516ce22cd75a38fd5cee6c572a7882 expected at /var/lib/docker/containerd/daemon/io.containerd.content.v1.content/blobs/sha256/68ca3975c1576d18f8cf52bcb6e153ce31516ce22cd75a38fd5cee6c572a7882: open /var/lib/docker/containerd/daemon/io.containerd.content.v1.content/blobs/sha256/68ca3975c1576d18f8cf52bcb6e153ce31516ce22cd75a38fd5cee6c572a7882: operation not supported`.
- Container disposition: `STOP_ORBSTACK_DAEMON_BLOB_READ`; no image pull/build, daemon restart, or repeat inventory attempt.
- Candidate invocations: 1; exit 0. Exact command: `python3 candidate.py --out formal_01/output`.
- Candidate stdout: `{"candidate_sha256": "e5fa444752df2bde82c9bc0bc28a6414329eb6855f290d6d050a14f3a453a1aa", "ledger_sha256": "a35eda129ccbbcf91ae317b758bd7f1b998cdbcb0637a66a05047a19f3741383", "record_count": 20, "records_sha256": "4e060fc709da0a0ea4cf50c98890b69337e36dfdcc2a4aa5cf6c78799c1fc38b", "schema": "unjuno.issue7487.t0.presentations.v1"}`.
- Independent auditor invocations: 1; exit 0. Exact command: `python3 auditor.py --out formal_01/output`.
- Auditor source SHA-256: `c492efcf7ec0f75d5df62df363987a40ad9b72737da138e08d5a9367896e2889`.
- Auditor result: 20/20 reconstructed; 0 errors; six effective mutations rejected (actor, action ID, target, effect ID, event order, causal-link status); unknown control remained `UNKNOWN`; `PASS_METHOD_SCOPED`.
- No candidate or auditor retry; no participant, model, GUI, app, user data, action dispatch, or product operation.
- After the formal pair, main advanced from the run base to `dd6b2c5307d412870e1f94df60de5021c57e0809` through two unrelated commits (#7502 tracked-backend integration). The publication branch was rebased without modifying the frozen package or formal output blobs; no experiment was repeated. `FREEZE.json` and this record keep the run's original base/source identity.
- Local checks after result capture: package contract `unittest` 1/1; repository sparse-checkout dependency test 1/1; analytical index 662/662; all retained SHA-256 entries verified; `git diff --check` clean. The analysis-index workflow now invokes the same package contract test on PR CI.

One construction-test command was initially invoked from repository root as
`python3 -m unittest -v research/analysis/delayed_gui_effect_attribution_7487_t0_20261004/test_contract.py` and failed to import the package-local `auditor` module (`ModuleNotFoundError`). No formal candidate had run. The same construction suite passed when run from its package directory; the failed invocation is retained here and was not treated as a scientific result.

Raw outputs and SHA-256:

| File | SHA-256 |
|---|---|
| `output/presentations.jsonl` | `4e060fc709da0a0ea4cf50c98890b69337e36dfdcc2a4aa5cf6c78799c1fc38b` |
| `output/candidate_manifest.json` | `ae8194bd381cf95a3f26f019b393152dbcf5561bd31fbce91d21024389acd4ca` |
| `output/audit.json` | `79c04972187e3b76ed394af94c8fae4cb90b6cc2e932a3c95c902872018dee7e` |

See `formal_01/` for exact captured command stdout/exit codes, host/runtime
metadata, and the separate OrbStack STOP receipt.

The renderings contain stipulated times and a synthetic delay field; no wall-
clock delay, GUI redraw, human exposure, attribution response, or confidence
was observed. This PASS is only a finite provenance/presentation method check.
