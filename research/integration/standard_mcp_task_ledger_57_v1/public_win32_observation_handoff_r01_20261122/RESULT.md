# Public Win32 observation measurement handoff R01

Status: `PASS_SYNTHETIC_SCHEMA_AND_RECORDER_JOIN`.

## Scope

The comparison measurement validator previously accepted local captures only
from guarded observation methods with a numeric `source.sequence`. The public
Win32 caller uses `interface_observe`, whose receipt identifies a capture with
an `observation_id`, `target_generation`, capture interval, and PNG artifact
digest. This candidate adds a separate capture-identity shape; it does not
reinterpret a timestamp or Relay request ID as a source sequence.

For `interface_observe`, the validator now requires one recorded MCP text
receipt and one PNG image block. It decodes the image bytes and checks their
SHA-256, byte count, artifact digest, observation ID, target generation,
matched-generation status, no-authority flags, and capture interval against
the local-observation record. The PNG digest must also appear in the retained
raw references. The recorder-adapter test writes those exact bytes into its
run root and passes the record through `build_measured_run`.

## Results

- The measurement and recorded-adapter suites pass **38/38** on CPython 3.11.9
  Windows, both normally and under `python -O`.
- The combined effect-handoff, reuse-horizon, post-authority attribution,
  comparison, and recorded-adapter suites pass **64/64** normally and under
  `python -O`.
- Positive coverage joins a public Win32 observation envelope to its exact
  PNG file and a recorded tool call.
- Negative coverage rejects changed observation ID, target generation, PNG
  bytes/digest, and image reference; existing guarded source-sequence
  observations remain covered.
- `git diff --check` passes. Exact conditions, source SHA-256 values, normal
  and optimized output, and the excluded wrong-directory discovery attempts
  are retained beside this report.

## Limits and next check

This is synthetic schema/adapter coverage. It does not claim that R05 has been
adapted: R05 contains only one public observation and lacks the exact
`interface_results` lookup plus a before/after capture pair needed for the
effect handoff. No live GUI input, model/provider call, Docker, WSLc, or
allocation was used. The new observation record is not yet joined to a specific
dispatch call's operation ID, independently scored task effect, release, and
neutral horizon. Next, add and test that composed evidence join, then freeze a
fresh standard-caller fixture run before considering any matched efficiency
block.

## Evidence

- Conditions and source hashes: [`conditions.json`](conditions.json)
- Normal run: [`raw/normal.log`](raw/normal.log)
- Optimized run: [`raw/optimized.log`](raw/optimized.log)
- Combined normal/-O integration: [`raw/integrated-normal.log`](raw/integrated-normal.log), [`raw/integrated-optimized.log`](raw/integrated-optimized.log)
- Excluded initial test-discovery attempts: [`raw/normal-wrong-directory-excluded.log`](raw/normal-wrong-directory-excluded.log), [`raw/optimized-wrong-directory-excluded.log`](raw/optimized-wrong-directory-excluded.log)
- Excluded first combined run without `PYTHONPATH`: [`raw/integrated-normal-missing-pythonpath-excluded.log`](raw/integrated-normal-missing-pythonpath-excluded.log), [`raw/integrated-optimized-missing-pythonpath-excluded.log`](raw/integrated-optimized-missing-pythonpath-excluded.log)
- Checksum manifest: [`SHA256SUMS`](SHA256SUMS)
