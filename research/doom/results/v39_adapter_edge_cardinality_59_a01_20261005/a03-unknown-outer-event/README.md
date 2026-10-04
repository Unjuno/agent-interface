# Unknown outer-event edge evidence — A03

## H / T / D / C / U

**H.** A row with an unknown outer event discriminator but a nested `physical_key_measurement.adapter_edge` is still adapter evidence. It must invalidate pairing for the matching program/step/key/token group; ignoring it can leave a duplicate DOWN or UP looking unique.

**T.** Freeze the exact #7602 source at base head `a7f9e9e3c4bd31199bde3a14761783ead619ad08`, retain the A01 raw DOWN/UP pair, then run both the existing exact-duplicate regression and four mutations: duplicate DOWN/UP with an unknown outer event, and single DOWN/UP rows whose outer event is unknown. Run the extracted tests against baseline and candidate source, then independently audit the raw identity, source/test hashes and red/green output.

**D.** Baseline must fail the two unknown-event duplicate cases because it still reports the unique original pair as complete. Candidate must pass both targeted test methods, including the existing exact-duplicate cases; the four new subcases must return exactly one incomplete receipt with null DOWN/UP timing.

**C.** Unknown events without `physical_key_measurement` remain unrelated and are ignored. An unknown event with that nested measurement is explicitly treated as possible edge evidence; the nested edge label selects the candidate side, and the outer discriminator must still be the corresponding supported `input_admission` or `input_release_measurement` name.

**U.** One synthetic retained A01 event pair and deterministic source projection only. No live X-server, physical dwell, application consumption, task effect, threat response, recovery, or MAP01 result is established.

The exact runner and independent audit are `run_a03.py` and `audit_a03.py`. Results, parent source, and SHA-256 manifest are retained alongside them. WSLc execution uses the pinned cached Python 3.12 image, `--pull never`, network disabled, one requested CPU, 512 MiB requested memory, nonroot UID/GID 1000, read-only source/evidence mounts, and a separate writable result mount. The host's unavailable swap/cgroup limit warning is retained; memory enforcement is not claimed.
