# Public Win32 effect-pair handoff R02

Status: `PASS_SYNTHETIC_PUBLIC_CAPTURE_EFFECT_JOIN`.

## Change

The research effect-receipt adapter now accepts either the existing guarded
capture reference (`source_sequence`, point timestamp) or a public Win32
capture reference (`observation_id`, target generation, capture start/end,
PNG digest). The public pair must use `interface_observe`, match the action's
target generation, and be recorded before dispatch and after the exact public
result lookup. The effect interval must fit strictly between the pre-capture
end and post-capture start. Existing guarded sequence ordering is unchanged.

This composes with the prior validator, which verifies the public MCP text
receipt, no-authority/no-input result, capture identity, and exact image block
bytes against a retained PNG. The effect receipt also joins one independent
task score, the same dispatch operation, exact `interface_results` response,
and verified release/neutral-horizon custody.

## Results

- Focused effect-receipt handoff: **19/19** normal and **19/19** under `-O`.
- Combined effect-handoff, reuse-horizon, post-authority attribution,
  comparison, and recorded-adapter suites: **67/67** normal and **67/67** under
  `-O`.
- The public Win32 positive case remains eligible only when the exact action
  generation is preserved and its independently observed effect interval lies
  inside authority. Negative cases reject a changed action generation and an
  interval extending beyond the post-capture boundary.
- Conditions, source hashes, full logs, environment, and manifest are retained
  in this packet.

## Limits

Synthetic only. This does not turn R05 into a task-score receipt: R05 has one
pre-action public observation, no exact `interface_results` lookup, no
before/after capture bracket, and public `task_success=null`. No live GUI
dispatch, provider/model call, Docker, WSLc, or allocation was used. The next
step is a fresh finite standard-caller fixture run using this full receipt
shape, then a separate recovery trial with the same custody discipline.

The initial test attempts that used an unset `PYTHONPATH` and a deliberately
inconsistent body/measurement generation are excluded and described in
[`raw/excluded-attempts.md`](raw/excluded-attempts.md); all final runs use the
repository root on `PYTHONPATH`.

## Evidence

- Conditions and source hashes: [`conditions.json`](conditions.json)
- Normal and optimized full suites: [`raw/normal.log`](raw/normal.log), [`raw/optimized.log`](raw/optimized.log)
- Runtime environment: [`raw/environment.txt`](raw/environment.txt)
- Excluded setup attempts: [`raw/excluded-attempts.md`](raw/excluded-attempts.md)
- Checksum manifest: [`SHA256SUMS`](SHA256SUMS)
