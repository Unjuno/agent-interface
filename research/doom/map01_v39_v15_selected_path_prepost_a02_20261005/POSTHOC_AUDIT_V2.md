# A02 retained-raw posthoc audit v2

This is a separate, versioned audit of the already retained A02 candidate output. It does not edit or replace `AUDIT.json`, does not rerun the frozen auditor, and does not rerun the candidate.

## Frozen inputs and invocation

- A02 source allocation remains frozen at base `81a59aed13492ba1d52ea80e03d48c3d8de7b2c5`; the current-main SHA observed before this posthoc audit was `018934cdf45fcabffcc4efe25b5c7b3d59bd459f`.
- Input: retained `run/candidate.stdout`; SHA-256 `0336cfa2eeebbe48ad816168d5466938a936fcf0782211b21847df6c20038596`. The retrieved bytes match the digest recorded by frozen audit v1.
- Candidate exit file parsed as `0`; the auditor applies the original whitespace-trimmed exit-file interpretation. Candidate stderr SHA-256 is the empty-file digest `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
- Auditor source SHA-256: `1ba31104625e37336baa3b9fd6834cf9b816c8e14639934b1eb13deac4e56359`.
- Host: Windows 11 Home, Python 3.11.9; standard library only.
- Invocation: `python audit_v2.py candidate.stdout.json candidate.exit candidate.stderr AUDIT_V2.json`.
- Candidate reruns: 0. Frozen auditor v1 reruns: 0. Posthoc v2 auditor invocations: 1.

## Result

`PASS_RAW_ONLY_POSTHOC_AUDIT_V2`: 39/39 checks passed. The auditor filters the emitted projection to rows whose event is `input_release_transition` before binding per-key receipts; it verifies route identity, event ordering, pre/post samples, telemetry order, owner receipt identity, scope flags, and both terminal cases. In the lost-SPACE case, post-sample and final fake-server state retain keycode 65, and cleanup records the expected fail-closed error.

The frozen v1 outcome remains `FAIL`, 21/32 checks, in the original `AUDIT.json`. That retained count corrects the PR description's earlier “11/32” wording. V2 does not retroactively change the preregistered result or make the candidate allocation PASS.

## Limits

This only checks retained JSON emitted by a fake X server. It does not establish physical keyboard state, real X11 delivery, application consumption, useful feedback, live latency, bounded recovery efficacy, threat response, or gameplay. XSync is server synchronization only; the private live-game lane remains unassigned.
