# Formal run record

- Allocation: `PATH-WIDTH-CONTINUOUS-GUI-6581-T0B-20261002-01`
- Base main: `60e2e7bb8a69cb7270fc2082e0affc5bf2789876`
- Freeze SHA-256: `addd830a46b938298a92e5709a9467e205515fc4347b4a42b20847f7a29dd2e6`
- The frozen root workflow source hash binds the exact workflow file in candidate branch commit `7d8cfa95fe8738f77bee876738b671dad828365d` at allocation time. Main advanced after the formal run; the PR integration carries newer unrelated index/workflow additions without rewriting this historical source identity.
- Platform: dedicated OrbStack Ubuntu 24.04 Noble ARM64 VM `research-path-width-6581-t0b-20261002`, own Docker Engine; formal candidate and auditor containers had network disabled and read-only root/source/dependency mounts.
- Candidate image: `mcr.microsoft.com/playwright@sha256:a51a0edc496f3e0cb386de2438eb1c2578de64cc7af60bfcbc7abfd410567fcd`; Playwright 1.55.1, Node 22.19.0, Chromium 140.0.7339.186.
- Auditor image: `docker.io/library/python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`.
- Locked Playwright dependency install: `npm ci --omit=dev`; `npm audit` reported 0 vulnerabilities. Dependency manifest SHA-256: `e9bdd79a82715aff461bf84b25b3654adc63e737d79a1cb18c9be37fa8bc34d4`.
- Candidate resource requests: 1 CPU, 1 GiB memory, 256 PIDs, 256 MiB `/dev/shm`, 128 MiB `/tmp`; auditor: 1 CPU, 512 MiB memory, 128 PIDs, 64 MiB `/tmp`. These are container requests/configuration, not a host-level resource benchmark.
- Formal counts: candidate process 1; auditor process 1; formal retries 0.

## Candidate

Command executed once inside the dedicated VM:

```sh
sudo docker run --rm --network none --cpus=1 --memory=1g --pids-limit=256 --read-only \
  --tmpfs /tmp:rw,nosuid,nodev,size=128m --shm-size=256m \
  --security-opt no-new-privileges --cap-drop ALL --workdir /src \
  --env PATHWIDTH_IMAGE_REF=mcr.microsoft.com/playwright@sha256:a51a0edc496f3e0cb386de2438eb1c2578de64cc7af60bfcbc7abfd410567fcd \
  --env RUN_ROLE=formal \
  --mount type=bind,src=/workspace/research/analysis/path_width_continuous_gui_6581_t0b_v1,dst=/src,readonly \
  --mount type=bind,src=/workspace/research/analysis/path_width_continuous_gui_6581_t0b_v1/construction_01/npmproj_1551/node_modules,dst=/deps/node_modules,readonly \
  --mount type=bind,src=/home/taka/pathwidth-formal-01,dst=/out \
  mcr.microsoft.com/playwright@sha256:a51a0edc496f3e0cb386de2438eb1c2578de64cc7af60bfcbc7abfd410567fcd \
  bash -lc 'node /src/run.mjs'
```

Exit code: 0. Candidate stdout reports 6 scenarios and event counts `5,5,5,6,6,6`; raw JSON SHA-256 `478a1ed7fc4fa92fb8c4b3c1c917d05ffef4643c54ac303ff02cf1c5c87ec450`.

## Independent auditor

One container-launch attempt with the mistaken image name `mcr.microsoft.com/library/python@sha256:...` failed before container creation/Python startup (`manifest unknown`); it was not an auditor-process execution. The exact pinned `docker.io/library/python@sha256:...` reference below was then used for the sole auditor-process execution. No candidate or auditor process was repeated.

```sh
sudo docker run --rm --network none --cpus=1 --memory=512m --pids-limit=128 --read-only \
  --tmpfs /tmp:rw,nosuid,nodev,size=64m --security-opt no-new-privileges --cap-drop ALL --workdir /src \
  --mount type=bind,src=/workspace/research/analysis/path_width_continuous_gui_6581_t0b_v1,dst=/src,readonly \
  --mount type=bind,src=/home/taka/pathwidth-formal-01/candidate.raw.json,dst=/evidence/candidate.raw.json,readonly \
  --mount type=bind,src=/home/taka/pathwidth-formal-01,dst=/out \
  docker.io/library/python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f \
  python3 -B /src/audit.py --raw /evidence/candidate.raw.json --spec /src/spec.json \
    --freeze /src/FREEZE.json --output /out/audit.json
```

Exit code: 0; stdout: `{"disposition": "PASS_METHOD_SCOPED", "rows": 6, "errors": []}`. Auditor JSON SHA-256 is listed in `SHA256SUMS.txt`.

## Evidence files

`candidate.raw.json`, `audit.json`, candidate/auditor stdout, stderr and exit-code receipts, and six scenario screenshots are retained in this directory. `SHA256SUMS.txt` binds the retained outputs. Formal evidence is distinct from the construction-only smoke artifacts.
