# Broker serve path rejection — #4921 result

## H / T / D / C / U

- **H:** A root-confined resolver wired into the host broker's real `serve()` request path should preserve valid aliases while rejecting unsafe schema/image/working paths before subprocess execution.
- **T:** Frozen allocation `broker-path-serve-rejection-4921-20260928-01`, main source blob `5734f54f318db9ac5e96b2bed6f6bed105ac39ff`, candidate/policy/runner/auditor hashes in [FREEZE.json](FREEZE.json). Executed one local Docker run on `python:3.13-slim@sha256:8d9d0b8bcf6506481eae4907c18f5e3e7902e629f5f6d684f9e7c32e85e3ddf0`, Linux/amd64, `--network none`, read-only root and source, private 16 MiB `/tmp`, 1 CPU, 256 MiB, 32 PIDs. The only subprocess was an in-process argument recorder.
- **D:** Frozen runner raw: 23/23 scheduled rows. Five accepts (two aliases, three in-root symlinks) each reached only the recorder once and mapped to canonical paths. Eighteen invalid cases (six classes × three fields) each produced `InvalidHostPath` / `HOST_MODEL_PATH_REJECTED`, `returncode=null`, `authority_granted=false`, and zero recorder calls. Raw-only audit v2: `PASS_INDEPENDENT_AUDIT_RAW_SCOPED`, errors=[], 6/6 corruption controls rejected. **Overall disposition: `HOLD_AUDIT_V1_EXCEPTION_AND_FIXTURE_NOT_RETAINED`**, not full PASS: frozen audit v1 raised `FileNotFoundError` because its independent audit ran after the runner's temporary fixture directory had been deleted. Posthoc audit v2 recovers the raw gate, but cannot independently `lstat/readlink` the vanished fixture tree. Its explicit limit is in [AUDIT_V2_FREEZE.json](AUDIT_V2_FREEZE.json) and [raw/AUDIT_V2.json](raw/AUDIT_V2.json).
- **C:** Only the candidate host-path mapping and rejection receipt handling differ from the frozen main broker. No host CLI, model, provider, or file read through the mocked broker occurred.
- **U:** Linux local-Docker construction/integration only; not Windows path parity, exploitability, a production broker fix, or #3152 live typed-vs-scalar/model-task acceptance. The production file remains unchanged.

## Retained outcomes

- Formal runner invocation: 1; retries/replays: 0.
- Raw SHA-256: `f24c17868fbb33fb1d9e8dd44624f986eaabbb1e2e9212f3bf77cd3850ec01e2`; see [raw/RAW.json](raw/RAW.json).
- Audit-v1 exception is preserved unchanged in [AUDIT_V1_EXCEPTION.json](AUDIT_V1_EXCEPTION.json).
- Posthoc audit-v2 SHA-256: `1aac076662a9ef7632f486bde11e0c4fa9005e67c17f0d77d3d4f1fc820f6d30`.
- Host and bounded Docker source-hash/compile preflight passed 5/5 frozen source files.
- No GPU/model work was needed; this path-policy question is deterministic and CPU-only.

## Reproduction

The exact source files and freeze are adjacent. Formal runner command (host paths substituted for the two mounted directories):

```text
docker run --rm --network none --read-only --tmpfs /tmp:rw,nosuid,nodev,noexec,size=16777216 --cpus 1 --memory 256m --pids-limit 32 -e PYTHONDONTWRITEBYTECODE=1 -v <source>:/src:ro -v <formal-output>:/out:rw -w /src python@sha256:8d9d0b8bcf6506481eae4907c18f5e3e7902e629f5f6d684f9e7c32e85e3ddf0 python runner.py /out/RAW.json
```

The separately frozen auditor-v1 STOP must remain preserved; do not rerun the formal allocation. Audit-v2 command:

```text
docker run --rm --network none --read-only --tmpfs /tmp:rw,nosuid,nodev,noexec,size=16777216 --cpus 1 --memory 256m --pids-limit 32 -e PYTHONDONTWRITEBYTECODE=1 -v <source>:/src:ro -v <formal-output>:/evidence:ro -v <audit-output>:/out:rw -w /src python@sha256:8d9d0b8bcf6506481eae4907c18f5e3e7902e629f5f6d684f9e7c32e85e3ddf0 python audit_raw_v2.py /evidence/RAW.json /out/AUDIT_V2.json
```

The temporary fixture directory was not persisted; v2 independently checks frozen fixture declarations and raw request/argv/receipt correspondence, not post-run filesystem identity. Any future stronger allocation must retain a read-only fixture manifest/inventory before execution and be frozen separately.
