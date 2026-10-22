# A15 raw-output custody handoff A01 (#59)

This evidence-only addendum repairs the public pointer and custody handoff for
the completed A15 allocation reported in [PR #8810](https://github.com/Unjuno/agent-interface/pull/8810).
It does not rerun or reinterpret A15. The original `AUDIT.json` remains FAIL;
the allocation disposition remains HOLD because the authored-cover health guard
was not exposed.

The original A15 result pointed at an ignored `results-local` path. The
reviewable aggregate is tracked at
[`A15_RESULT_PUBLIC.json`](../map01_v39_live_threat_guard_a15_health_policy_guard_a01_20261009/A15_RESULT_PUBLIC.json).
Its SHA-256 is identical to the local public summary in the retained A15 output.
The complete raw output remains local. This package publishes only each
relative path, byte size, and SHA-256 in `A15_RAW_SHA256_MANIFEST.jsonl`; it
contains no raw protocol, prompt, frame, or session contents.

The manifest inventories 3,859 files totaling 119,669,935 bytes. The
hash-bound readback records the manifest digest, the raw `FREEZE.json`, original
`AUDIT.json`, private result record and public summary digests, plus the exact
tracked summary path and revision. The verifier checks every local file,
rejects missing/extra/changed files and unsafe paths, and confirms the local
public summary matches the tracked file at the recorded PR #8810 revision.

## Verification

Set `RAW_ROOT` to the already retained A15 output directory and `A15_CHECKOUT`
to a checkout containing PR #8810 head `3766e880ca0d52652dc9cc3d7caac766aef716f8`.
Then run from the repository root:

```sh
python3 research/doom/a15_raw_custody_handoff_a01_20261009/verify_manifest.py \
  --raw-root "$RAW_ROOT" \
  --manifest research/doom/a15_raw_custody_handoff_a01_20261009/A15_RAW_SHA256_MANIFEST.jsonl \
  --readback research/doom/a15_raw_custody_handoff_a01_20261009/A15_CUSTODY_READBACK.json \
  --public-summary "$RAW_ROOT/A15_RESULT_PUBLIC.json" \
  --public-repo "$A15_CHECKOUT" \
  --public-revision 3766e880ca0d52652dc9cc3d7caac766aef716f8
PYTHONPATH=research/doom/a15_raw_custody_handoff_a01_20261009 \
  python3 -m unittest discover \
  -s research/doom/a15_raw_custody_handoff_a01_20261009 \
  -p 'test_*.py' -v
```

The retained local validation returned `PASS_A15_RAW_CUSTODY`, 3,859/3,859
files and 119,669,935 bytes; the four verifier tests pass. No candidate, game,
model, GUI, or OS input was invoked.
