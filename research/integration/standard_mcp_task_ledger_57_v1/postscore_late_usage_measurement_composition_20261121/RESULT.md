# Attempt 01 — harness preflight failed

- Frozen source: `d08596ee0590ba6a9531075a5769c0ac4abc1ec1`.
- Normal unittest run: 0/2 passed. Both failures are preserved in
  `windows-py311-normal.log`; exit code is `1`.
- The positive fixture omitted the required `observed_ns` field in its
  synthetic App Server JSONL row. The negative fixture omitted the
  comparison adapter's required `effect_attribution` field.
- The experiment runner was not executed, so no positive/negative run was
  consumed. The `-O` test suite was not run after the normal preflight failed.
- No provider, Relay, GUI, OS input, Docker, or WSLc operation occurred.

This is a harness-construction failure, not a product or provider result. The
frozen conditions and pass rule are unchanged. Attempt 02 is a separate packet
that supplies the required timestamped synthetic row and an explicitly
nonphysical, unknown-effect schema envelope; it does not claim task success or
input release.
