# Needle role-conditioned online LoRA rehearsal

Research-only three-arm test of a 16-example A rehearsal memory during online B corrections. No runtime or product code changes.

## Construction

Use the exact image pinned in `FREEZE.json` with Docker `--pull=never`, `--network=none`, `--read-only`, `--cpus=1`, `--memory=2g`, `--pids-limit=64`, no-new-privileges and a 64 MiB tmpfs. Mount this source read-only at `/src`, work in `/src`, then run:

```powershell
docker run --rm --pull=never --network=none --read-only --cpus=1 --memory=2g --pids-limit=64 --security-opt=no-new-privileges --tmpfs /tmp:rw,noexec,nosuid,size=64m --mount "type=bind,source=<source-dir>,dst=/src,readonly" --workdir /src -e PYTHONDONTWRITEBYTECODE=1 sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e -m unittest -v test_construction
```

Tests import the independent auditor and producer but perform no optimizer updates. The role bit makes the opposing A/B label functions representable; this is intentionally not the unconditioned task from #4888.

The full excluded construction seed 735014 is run separately with `construction.ps1` into its own empty output directory. It is not pooled with the formal seeds. The retained construction raw was independently audited twice (the second audit also explicitly checked post-training base immutability); both reports and all logs remain separate. A wrapper attempt that stopped before the first fit is also preserved as a prefit construction STOP.

## Formal

Freeze every source file and record all preregistration hashes before formal execution. Use `formal.ps1` once with an empty output directory. It validates source/image/seeds before launch and binds exact retained raw/stdout/stderr bytes into `FORMAL_INVOCATION.json`. Do not rerun allocated seeds. The audit accepts arbitrary host output directory names and checks container mount destinations rather than a fixed local path.

Run `audit.ps1` exactly once using a distinct empty audit output directory. It mounts source and formal output read-only and reconstructs the base, splits, training schedules, adapter/AdamW states and held-out predictions without importing `runner.py`. Audit failure is HOLD; valid quality miss is FAIL; no post-result change can upgrade either.
