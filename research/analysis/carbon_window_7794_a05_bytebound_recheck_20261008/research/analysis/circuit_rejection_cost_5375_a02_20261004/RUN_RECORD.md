# A02 run record

## Freeze and preflight

Allocation `CIRCUIT-REJECTION-COST-5375-A02-20261004-01`; current main at freeze and immediately pre-formal check `13bab54ea6d91978247ecc1b70e5060db752367a`. The only matching open branch/PR before formal run was the retained A01 evidence branch/PR #7391; no A02 path/owner existed. Issue preregistration: #5375 comment 5975869308. `FREEZE.json` binds all sources and runtime.

Construction preflight ran in WSLc, separately from the formal candidate/auditor: `python -B -m unittest -v test_preflight.py` — 6/6 passed. It checks capacity, obligation conservation, zero authority, independently reconstructed raw, decision controls, and explicit ineligible planted-drop row.

## Formal candidate

Immediately beforehand `wslc container list` reported no running containers.

```text
wslc run --rm --name cir-rej-a02-candidate --pull never --network none --cpus 1 --mount type=bind,source=<experiment-a10>,target=/src,readonly --mount type=bind,source=<experiment-a10-output>,target=/out --workdir /src python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f python -B candidate.py spec.json /out/raw.jsonl
```

Exit 0; `CANDIDATE_COMPLETE`; 10 rows.

## Formal independent audit

Immediately beforehand `wslc container list` again reported no running containers.

```text
wslc run --rm --name cir-rej-a02-auditor --pull never --network none --cpus 1 --mount type=bind,source=<experiment-a10>,target=/src,readonly --mount type=bind,source=<experiment-a10-output>,target=/out,readonly --mount type=bind,source=<experiment-a10-audit>,target=/audit --workdir /src python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f python -B auditor.py spec.json /out/raw.jsonl /audit/audit.json
```

Exit 0. Exact reconstruction: 10 rows, `errors=[]`; outcome `PASS_METHOD_SCOPED`; 7/7 decision checks; mutation rejection 4/4; authority admissions 0. After completion the container list was empty. Candidate=1; auditor=1; retries=0. WSLc emitted no cgroup/swap warning in captured command output; no hard memory enforcement is inferred.
