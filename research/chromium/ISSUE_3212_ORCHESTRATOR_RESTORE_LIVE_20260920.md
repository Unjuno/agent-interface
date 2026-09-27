# Issue #3212 — live orchestrator restart with new browser generation (2026-09-20)

Additive successor evidence. Existing owner-exit, HOLD, STOP, and adversarial records are unchanged.

## H/T/D/C/U

- **H:** After an orchestrator/container restart, a persisted receipt from generation 1 must remain unusable; a newly launched browser resource must obtain generation 2 and only that new receipt may cause an application effect.
- **T:** Three independent A→B allocations. Container A used the real Chromium fixture under Docker `--network none`, Xvfb, and CDP, wrote a persisted receipt, and exited. Container B used the same image and shared volume, loaded A's receipt, launched a fresh real Chromium resource, checked process-start epochs, rejected the old receipt, and dispatched the new receipt through the DOM application route. An independent auditor ran in a separate Docker invocation.
- **D:** `PASS_ORCHESTRATOR_RESTORE_AUDIT rows=6 allocations=3 errors=0`. Old receipt admission was `0/3`; new receipt admission was `3/3`; independent DOM effect was `3/3` with `title=saved:abc`, `saved=true`, `value=abc`. A→B `/proc/<pid>/stat` start ticks increased in all runs: `3414740→3414932`, `3415159→3415354`, `3415558→3415746`. Raw SHA-256: `49b3f5b5c37f5d31e65f3502c08cc6cd211eccb8fa158841e7df820db4437e4`.
- **C:** `PASS_CHROMIUM_ORCHESTRATOR_RESTORE_NEW_GENERATION_SCOPED`. The old persisted receipt fails closed across the restart while a new generation can be re-established and produce a real DOM effect in this fixture.
- **U:** This does not establish production orchestrator semantics, graceful restoration of every browser state, model benefit, or cross-application generalization. The fixture uses an explicit shared-volume restart and a new receipt; those boundaries remain in force.

## Exact execution

Image: `mixed-formal-2992-debian@sha256:766abfd10382ab8b59ed793094a685481190f840d338b7bc4664ca162a2da619`.

Each allocation ran:

```text
docker run --rm --network none \
  -v <fixture>:/fixture:ro -v <state>:/state:rw \
  --entrypoint /usr/bin/python3 mixed-formal-2992-debian:20260920 \
  /fixture/orch.py A
docker run --rm --network none \
  -v <fixture>:/fixture:ro -v <state>:/state:rw \
  --entrypoint /usr/bin/python3 mixed-formal-2992-debian:20260920 \
  /fixture/orch.py B
```

The committed runner, raw JSONL, and independent auditor are under `research/chromium/issue-3212-orchestrator-restore-v1/`.
