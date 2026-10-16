# Host construction result — T0-01

**Disposition:** `PASS_SYNTHETIC_OWNER_BRACKET_JOIN_SCOPED`.

The one frozen-source candidate invocation successfully used the current-main `InputOwner v10` worker queue and `InputOwner v11` caller wrapper with fake Xlib. The independently authored raw-only audit accepted all six retained rows with `errors=[]`.

The single explicit release was identity-bound in the harness to owner `f10f8c74b8d74a22bf0d0cab6ac35988`, intent `host-t4-intent-01`, key `a` / keycode 38. Observed monotonic timestamps were:

- caller start: `111280439629900 ns`
- fake owner-thread KeyRelease request: `111280439654700 ns`
- fake owner-thread sync return: `111280441984300 ns`
- caller return: `111280442036400 ns`
- caller interval width: `2,406,500 ns`

Thus this one fake-backend execution satisfies `caller_start <= owner_release_request <= owner_sync_return <= caller_return`. Fake key state transitioned down→up, the owner thread terminated, and all authority/physical-observation/application-consumption claims remained false.

This is a host-only construction PASS. The XTest request, sync, and key state came from the fake backend; no X server or physical keymap was involved. It does not satisfy #5156's isolated X11 gate or #59's live-control objective. No container, GUI, game, model, GPU, or user input was used.

See `raw.jsonl`, `audit.json`, and `RUN_RECORD.md`; all are covered by `SHA256SUMS`.

The final result directory has five files: `raw.jsonl`, `audit.json`, this report, `RUN_RECORD.md`, and `SHA256SUMS`. The frozen method note's anticipated count of three files was imprecise; it was not a decision gate, and no first-outcome bytes were changed.
