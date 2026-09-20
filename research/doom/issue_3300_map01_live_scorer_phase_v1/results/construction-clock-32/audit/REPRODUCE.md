# Independent audit reproduction

Run from repository root, using the isolated arm64 image
`agent-interface-map01-clock-review-fixed:20260920b`, image ID
`sha256:08e8b41ebd1476eff067939e0192d49e4014c21bab11a4d793429187e4242704`:

```sh
docker run --rm --platform linux/arm64 --network none --read-only \
  --workdir /work --tmpfs /tmp:rw,noexec,nosuid,size=128m \
  -v "$PWD/research/doom/issue_3300_map01_live_scorer_phase_v1:/work:ro" \
  -v "$PWD/research/doom/issue_3300_map01_live_scorer_phase_v1/results/construction-clock-32:/result:ro" \
  --entrypoint python agent-interface-map01-clock-review-fixed:20260920b \
  -m unittest -v test_audit_engine_tic_debug_construction

docker run --rm --platform linux/arm64 --network none --read-only \
  --workdir /work --tmpfs /tmp:rw,noexec,nosuid,size=128m \
  -v "$PWD/research/doom/issue_3300_map01_live_scorer_phase_v1:/work:ro" \
  -v "$PWD/research/doom/issue_3300_map01_live_scorer_phase_v1/results/construction-clock-32:/result:ro" \
  --entrypoint python agent-interface-map01-clock-review-fixed:20260920b \
  -m unittest -v test_audit test_audit_passive_process_activity test_audit_engine_tic_debug_construction
```

The retained full test output is `../test-container.log` (23 tests, OK).
Recompute the raw/log digests from `../raw.json` and `../container.log` before
running the auditor. The audited capture remains fixed; reproduction tests
exercise the parser and gate, they do not regenerate the scientific capture.

Auditor command (writes only to the container's ephemeral `/tmp`):

```sh
docker run --rm --platform linux/arm64 --network none --read-only \
  --workdir /work --tmpfs /tmp:rw,noexec,nosuid,size=128m \
  -v "$PWD/research/doom/issue_3300_map01_live_scorer_phase_v1:/work:ro" \
  --entrypoint python agent-interface-map01-clock-review-fixed:20260920b \
  /work/audit_engine_tic_debug_construction.py \
  /work/results/construction-clock-32/raw.json \
  /work/results/construction-clock-32/container.log /tmp/audit.json
```
