# Run record — PREVIEW-CONSTRAINT-PARITY-6565-ORB-T0-20261002-01

- Issue: #6565, additive T0 method-stage card parity.
- Intake main: `a28fd4456ebfd0c181e14e5f018627d7e57b856a`.
- Source commit: `5d584c4723af48a628fbba9aa88c6ba6dbcdcbeb`.
- Freeze commit: `c126615cc98a3f672075e30840ad7b8640c6c2ba`.
- Freeze JSON SHA-256: `4abd3ce8a4a315daf498e0d1566c5a027d47ee69a262bfa90c3fb2110ca9df37`.
- Runner command: `python3 -B research/analysis/preview_constraint_parity_6565_t0_20261002/runner.py`.
- Context/image: OrbStack; cached `python:3.12-slim-bookworm@sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e`, image ID same SHA, `linux/arm64`; pull never.
- Candidate container: `preview6565-candidate-formal01-20261002`, ID `4a4f9982ff7f253b9c7f8bbe688ba7fc5dcfbc18817f1b55947a45e18b2809a0`, exit 0.
- Auditor container: `preview6565-auditor-formal01-20261002`, ID `cfa522b2cf90e2b07b481de3b263109256b348e8b8f697d7132f7a9ac3b5cade`, exit 0.
- Runtime config: network none; read-only root; source read-only; candidate raw and audit output on separate writable mounts; CPU 1; memory 268,435,456 bytes requested; PIDs 64. Both inspect receipts report exit 0, `OOMKilled=false`, network `none`, read-only root, 1 CPU, memory 268,435,456, PIDs 64.
- Formal counts: candidate 1, auditor 1, retries 0.

## Commands executed in formal containers

Candidate:

```text
docker run --name preview6565-candidate-formal01-20261002 --pull never --network none --cpus 1 --memory 256m --pids-limit 64 --read-only --mount type=bind,source=<package>,target=/src,readonly --mount type=bind,source=<formal_01/candidate>,target=/out --workdir /src <pinned-image> python -B /src/candidate.py --out /out/raw.json
```

Auditor (candidate input mounted read-only):

```text
docker run --name preview6565-auditor-formal01-20261002 --pull never --network none --cpus 1 --memory 256m --pids-limit 64 --read-only --mount type=bind,source=<package>,target=/src,readonly --mount type=bind,source=<formal_01/candidate/raw.json>,target=/input/raw.json,readonly --mount type=bind,source=<formal_01/auditor>,target=/out --workdir /src <pinned-image> python -B /src/auditor.py /input/raw.json --out /out/audit.json
```

The exact absolute argv and combined logs are retained in the machine `RUN_RECORD.json` and each stage directory. Candidate raw: 12,292 bytes, SHA-256 `14214d109b9705f28345e30385fe59934afd45971c354edde5b5f77b21a92ac9`. Audit JSON SHA-256 `671984baafab1aca2acd370d523b07874e69d228a7c2814612c1b23592d4f4cd`.

## Outcomes

Candidate reported 12 rows (exit 0). Independent raw-only auditor reported `PASS_METHOD_SCOPED`, 12 rows, zero errors (exit 0); 12/12 unique keys and six mutation classes rejected. Construction tests passed 8/8 on host and 8/8 in a disposable OrbStack container before formal freeze. No formal command was retried. See `REPORT.md` for interpretation boundaries.
