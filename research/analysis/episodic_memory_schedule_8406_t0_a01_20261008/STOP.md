# Issue #8406 T0 A01 — terminal formal STOP

## Disposition

`STOP_AUDITOR_KEYERROR_SCHEDULE_SHAPE`. The frozen candidate ran once and exited 0. The frozen auditor was invoked once and exited 1 before writing `AUDIT.json`. Retries/replacements: 0. This is an auditor execution defect, not a scientific FAIL and not a schedule-sensitivity result.

## Retained evidence

- Frozen source commit: `33027b28b4`.
- Candidate raw: `formal_01/RAW.json`; SHA-256 `2c79a10fa6530d74ac17ea9c67816b9517c63235a4cd32fcf70a2d463d4d9f70`.
- Expected counts printed by candidate: 12 source episodes; visibility rows 16 per arm; update counts episodic-only 0, per-episode 12, batch-of-4 3, terminal 1.
- Auditor `AUDIT.json` was not created because the uncaught exception occurred before result serialization.

Exact auditor exception output:

```text
Traceback (most recent call last):
  File "/private/tmp/agent-interface-7452-ordered-context-a01/research/analysis/episodic_memory_schedule_8406_t0_a01_20261008/audit.py", line 150, in <module>
    main()
  File "/private/tmp/agent-interface-7452-ordered-context-a01/research/analysis/episodic_memory_schedule_8406_t0_a01_20261008/audit.py", line 124, in main
    controls = hostile_controls(raw, expected)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/agent-interface-7452-ordered-context-a01/research/analysis/episodic_memory_schedule_8406_t0_a01_20261008/audit.py", line 77, in hostile_controls
    first_ref = mutant["schedules"]["per_episode"][0]["episode_refs"][0]
                ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^
KeyError: 0
```

## Cause and boundary

The candidate encodes each arm under a schedule-name key, while the frozen auditor's hostile-control harness indexes `per_episode` as if it were a list. This is a constructor/validator interface mismatch in the auditor's mutation stage. No raw reconstruction verdict, mutation-control result, or scientific inference was produced. A separately frozen successor may correct the auditor; this A01 source, raw, and STOP remain unchanged.
