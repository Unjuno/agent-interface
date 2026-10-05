# Safe rerun

The historical `executed-runner.py` writes to the tracked `raw-differential.json` using a fixed experiment identifier. Do not rerun it in this package directory.

Use the safe wrapper from a clean checkout of the source revision to create a fresh run directory outside both the source checkout and this package:

```sh
python3 /path/to/this/package/rerun_safely.py \
  --source-root /path/to/agent-interface-checkout \
  --output-root /path/to/separate-evidence-directory
```

Each run receives a UUID directory created exclusively; a collision is refused before candidate execution. The wrapper copies the frozen candidate and auditor into that directory, captures their stdout and stderr separately, and writes `RUN.json` with source revision, runtime, provenance, exit codes, before/after source hashes, and artifact hashes. Each process has a 120-second default timeout (`--timeout-seconds` can lower or raise it); timeout and launch failures are recorded, including any partial stdout/stderr. The original frozen runner and tracked raw evidence remain unchanged.

The included runs demonstrate only synthetic raw reconstruction and audit on their recorded source checkouts. `test_rerun_safely_timeouts.py` checks that candidate and auditor timeouts retain a terminal record and partial output. It provides no desktop GUI, model, input-effect, latency, or integrated-comparison evidence for issue #3311.
