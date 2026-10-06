# Reproduce the retained audit without replaying input

Use any Python 3.11+ interpreter in an environment you own. The audit takes explicit input and a **new output file**. It reads the committed raw and source lock and never runs X11, candidate code, or model calls. Do not direct output to committed `run-01/audit.json`.

```bash
python3 /path/to/package/audit_native.py.txt \
  /path/to/package/run-01/raw.json \
  /path/to/package/source-lock.json \
  /new/disposable/output/audit.json
```

The expected retained result is 658/658 logical checks, exit 0. Independently verify every entry in `manifest.json` before relying on this result; that manifest deliberately excludes itself. Re-running a raw audit is not another experimental trial.

For the 8 mutation controls, copy this package to a fresh disposable directory, copy `audit_native.py.txt` to `audit_native.py`, and copy `audit_mutations.py.txt` to `audit_mutations.py`. In that disposable copy only, choose a new output path in the mutation script (the retained `audit-mutations.json` is exclusive and must not be overwritten). Execute with `PYTHONDONTWRITEBYTECODE=1`. The original raw is mutated only in memory. All eight corruptions must be rejected.

## Executed-source reconstruction

The candidate uses `source-lock.json` head `2b0cb591c3ebcb84d1db983612613850c08fffea` from the same repository. For each of the 81 manifest rows, read `git show <head>:<path>` as raw bytes into a new `source/<path>`, verify its SHA256/byte count, and verify `git rev-parse <head>:<path>` equals the recorded Git blob. No current working-tree source is substituted. The two non-Python resources and the 79 Python blobs remain at their repository-relative paths. The constructor loads 32 modules; export inventory and execution coverage are different.

`native_probe.py.txt` and `audit_native.py.txt` are the exact frozen Python files with inert archive suffixes. To examine or construct a new authorized native test, copy them as `.py` into a new directory beside `source/` and `source-lock.json`. The fixed sys.path order and `ProbeLease`/manual step context are in the driver. Required Debian package versions are in `package-inventory-final.tsv`; no mutable image tag is claimed as a content digest.

`run-01-request.json` retains the exact completed command, including the owned VM, non-root user, private Xvfb display, cgroup caps, source/output layout, and runtime limit. `prepare_and_run.py.txt` retains the original host orchestration, exclusive freeze/request/result writes, transfer and verification; it is a record, not a portable automatic launcher. The VM was stopped after the run. A future native run requires a fresh valid resource decision, output directory and invocation record, and must retain any failure. Do not reuse this run ID or treat reconstruction instructions as a live-game allocation.
