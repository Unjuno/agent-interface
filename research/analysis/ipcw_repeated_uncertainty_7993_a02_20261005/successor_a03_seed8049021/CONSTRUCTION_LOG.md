# A03 construction and preflight log

- A02's original formal `docker run` was rejected by the local Docker CLI because its writable `--mount` included invalid bare field `rw`. A02 STOP is preserved unchanged; no candidate/auditor ran there.
- First A03 mount-smoke attempt referenced the intentionally sparse/unmaterialized A02 protocol path and stopped before the container started (`bind source path does not exist`). Its first stdout/stderr are retained as `preflight-setup-stop.*.txt`; no candidate/auditor was invoked. The preflight was corrected to use A03's own present protocol file, not to rerun the same failed command.
- Corrected A03 mount smoke passed on the pinned image: read-only source yielded 2,663 bytes; the default read-write output bind created `mount-smoke.txt`; exit 0, stderr empty. `PREFLIGHT.json` captures command and hashes.
- Candidate/auditor formal calls remain 0/0. Construction tests are run before A03 freeze. Formal fixture seed 8049021 is separate from the A02 stopped seed 8049020 and all four pilot seeds.
