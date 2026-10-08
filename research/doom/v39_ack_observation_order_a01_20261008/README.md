# V39 acknowledgement and typed-observation order A01

This paired construction varies only the order of a typed health-drop row and a fake executor acknowledgement while exercising the exact frozen V39 `wait` helper. It distinguishes the queue order that loses the typed row from the order that leaves it for the later monitored wait. No executor binary, GUI, game, OS input, or live allocation is used.

The initial audit-test STOP is retained in `A01_INITIAL_TEST_FAILURE.txt`; its first audit output is retained as `AUDIT.json`, and the subsequent pre-v2 audit rerun is `AUDIT_V2_INITIAL.json`. The candidate raw is unchanged. Audit v2 adds explicit rejection of unsupported executor/input claims; all five mutation tests then passed under normal Python and `python -O`.

## H / T / D / C / U

- **H:** If the typed row is ahead of acknowledgement, the unmonitored wait discards it; if acknowledgement is ahead, the following monitored wait receives and invalidates on the row.
- **T:** Run two deterministic schedules with identical rows and production helper; change only their order around acknowledgement.
- **D:** Pass only if the two event traces differ exactly at that monitor boundary as preregistered.
- **C:** Queue-order sensitivity does not establish which order occurs in the real controller or whether any executor input occurs before invalidation.
- **U:** No queue arrival timing distribution, executor acceptance, input emission, live threat, key release, recovery, or task outcome is measured.

## Reproduction

```text
python -m research.doom.v39_ack_observation_order_a01_20261008.candidate
python -m research.doom.v39_ack_observation_order_a01_20261008.audit_v2
python -m unittest -v research.doom.v39_ack_observation_order_a01_20261008.test_audit
```
