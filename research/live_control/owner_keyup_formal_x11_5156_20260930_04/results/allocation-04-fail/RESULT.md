# Allocation 04 result: runner failure (no formal verdict)

- Issue/allocation: #5156, MAP01-OWNER-KEYUP-BRACKET-5156-20260930-04
- Window: 2026-09-30 16:00–16:15 UTC
- Frozen baseline: `bc57d55d4e0a4e75d1945d541ed27fce7cb2b955`
- Candidate branch checkout: `1bfbae8e9e74bafda3f8c2200076a62d6eabff7a`
- Image: `sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27`, linux/arm64
- Runner: `run_formal_x11.py`, frozen hash `ba24bb7795fec409b30c4a2c7b5362d552a1d70bd1097a52b7160e2ea069b54a`
- Container exit: 1

## Observed

The runner executed the single-key, two-key, and partial-cancel sequences. It recorded verified key-down admissions and verified all-keys-up terminal states; partial cancel also recorded rejection of the second admission. It then failed while serializing joined release rows:

```
TypeError: dict() got multiple values for keyword argument 'event'
```

The failure is caused by `dict(event="joined_release", **row)` when `row` already has an `event` field. The exception occurred after the input sequences; release-bracket rows were not serialized.

## Verdict boundary

This is a runner failure, not a candidate PASS or a formal safety FAIL. The one-shot allocation was consumed. The independent auditor was not run because the frozen protocol permits it only after runner exit 0. No runner completion record or formal audit exists. Do not retry this allocation; repair the serializer only in a successor allocation with a new authorization/window, preserving this result unchanged.

## Isolation and evidence

The run used the authorized OrbStack context, pinned image with `--pull=never`, `--network none`, one CPU, 512 MiB memory, PID limit 64, read-only root, and a temporary `/tmp`. Source was mounted read-only and results were written to a separate bind mount. Docker used `--rm`; the container list was empty after exit. The Xvfb process was also confirmed stopped.

Evidence files are the raw JSONL, runner stdout/stderr, and Xvfb log in this directory. SHA-256:

- `raw.jsonl`: `564f4c053cf8a0114a3bb7fd4a7eae166ec7516318bbf4972759eaec6eb92ec6`
- `runner.stderr.txt`: `88be776849bd21336b2c56df3b308539e7cd85b84bd4751cafc5163483ba0be5`
- `runner.stdout.txt`: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` (empty)
- `xvfb.log`: `b987a262609a3720f450ab6815ed90b2069dd47b7b012959ca19c325eabf5d55`

Pre-run local auditor tests passed 8/8. They do not compensate for the missing formal audit. No changes were made to the frozen runner, expected results, or prior allocations.
