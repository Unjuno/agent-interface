# One-shot formal commands

Run from the repository root after verifying both output paths are absent.
The candidate receives only its script and candidate-visible input as
individual read-only mounts. It does not receive the auditor oracle. The
auditor gets the package read-only and the candidate raw output, and emits its
audit on stdout for exclusive host-side capture.

```sh
PKG=research/analysis/clarification_timing_5959_t0_a01_20261008
docker run --name ai5959-t0-a01-candidate-20261008 --pull=never --platform linux/arm64 --network none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=16m --cpus=0.5 --memory=256m --pids-limit=32 --cap-drop=ALL --security-opt=no-new-privileges --user 65532:65532 --workdir /tmp --mount "type=bind,source=$PWD/$PKG/candidate.js,target=/tmp/candidate.js,readonly" --mount "type=bind,source=$PWD/$PKG/candidate_inputs.json,target=/tmp/candidate_inputs.json,readonly" node@sha256:0b36e8c136b94cd4fcf02188228e76c31ad5872eef3fec8cbd2eee500cfd9e80 node /tmp/candidate.js --formal /tmp/candidate_inputs.json > "$PKG/formal_01/RAW.json" 2> "$PKG/formal_01/STDERR.log"
```

After confirming the raw JSON parses and candidate exit status is zero, run the
auditor exactly once:

```sh
docker run --name ai5959-t0-a01-auditor-20261008 --pull=never --platform linux/arm64 --network none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=16m --cpus=0.5 --memory=256m --pids-limit=32 --cap-drop=ALL --security-opt=no-new-privileges --user 65532:65532 --mount "type=bind,source=$PWD/$PKG,target=/pkg,readonly" node@sha256:0b36e8c136b94cd4fcf02188228e76c31ad5872eef3fec8cbd2eee500cfd9e80 node /pkg/auditor.js --formal /pkg /pkg/formal_01/RAW.json > "$PKG/audit_01/AUDIT.json" 2> "$PKG/audit_01/STDERR.log"
```

No retry is permitted. Any nonzero exit, missing output, hash mismatch, or
existing one-shot output is retained as the first STOP/FAIL, with counts
reported literally.
