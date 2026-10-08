# Formal invocation record — Issue #4834

The source was mounted read-only in both containers. The raw output directory
was freshly created before training; the audit directory was freshly created
before the separate audit. Both commands ran locally on the attached PC against
the already-cached image; Docker used no network and did not pull or install.

Trainer, exit code 0, exactly once:

```text
docker run --rm --pull=never --network none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=512m --memory=2g --cpus=1 --pids-limit=64 --security-opt=no-new-privileges -e PYTHONPYCACHEPREFIX=/tmp/pycache -v <frozen-source>:/src:ro -v <fresh-raw-output>:/out:rw --entrypoint python3 needle-pilot05:local /src/needle_frontier_study.py --output /out/raw.json
```

Independent auditor, exit code 0, exactly once, with raw mounted read-only:

```text
docker run --rm --pull=never --network none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=512m --memory=2g --cpus=1 --pids-limit=64 --security-opt=no-new-privileges -e PYTHONPYCACHEPREFIX=/tmp/pycache -v <frozen-source>:/src:ro -v <raw-output>:/raw:ro -v <fresh-audit-output>:/audit:rw --entrypoint python3 needle-pilot05:local /src/needle_frontier_audit.py /raw/raw.json --output /audit/audit.json
```

No retries, reruns, replacement seeds, post-result training, tuning, GPU,
external workflow, GUI, provider, or user data were used. Both processes emitted
the PyTorch warning that NumPy is absent in the image; no code path here needs
NumPy, and training plus independent auditing exited successfully.
