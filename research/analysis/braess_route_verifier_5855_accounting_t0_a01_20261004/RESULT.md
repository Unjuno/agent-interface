# #5855 queue-conservation controls A01

**Scoped result: PASS_ACCOUNTING_CONTROLS_SCOPED.** This host-CPython method
experiment checked the proposed finite-window accounting controls against
five frozen synthetic event traces. Candidate and raw-only independent auditor
each ran once; there were no retries. This is neither a live queue/runtime
result nor evidence for the #59 gameplay gate.

## H / T / D / C / U

- **H:** Event-by-event task conservation, explicit censoring and unique receipt
  identity distinguish verified work from apparently faster complete-only
  samples, duplicate retry receipts, and transient finite windows.
- **T:** Allocation
  BRAESS-QUEUE-ACCOUNTING-5855-T0-20261004-A01; frozen main
  9dc383a89043deb6199c847196498d867ba6bb75; five traces / 47 events:
  matched complete baseline and route-added arms, duplicated retry receipt,
  transient startup window, and stable periodic control. Four construction
  mutation/unit tests passed before the source freeze.
- **D:** Independent audit exited 0 with all 8 top-level checks true and
  PASS_ACCOUNTING_CONTROLS_SCOPED. Every accepted trace snapshot conserves
  offered task IDs across verified, rejected, skipped, queued, in-service and
  lost states. The intentionally malformed duplicate trace was rejected for
  both duplicate receipt identity and duplicate/unmatched terminal transition.
- **C:** In the matched pair, all four offers/arrival ticks are unchanged.
  Baseline verified 4/4 (mean sojourn 3.5 ticks). Route-added verified only
  2/4 by horizon 10; its complete-only mean is 1 tick, but t2 and t3
  remain censored. That apparent 3.5→1 improvement is not a denominator-
  complete system improvement.
- **U:** Synthetic deterministic queue fixtures only; no production route,
  model/provider, GUI, game, input, GPU, or real task effect was exercised.

## Finite-window controls

| Trace | Independently reconstructed result |
|---|---|
| Matched baseline | 4/4 verified; no censored task; all event ledgers conserve |
| Route added | 2/4 verified, censored {t2,t3}; complete-only mean 1 tick versus 3.5 baseline, explicitly not comparable as full completion |
| Duplicate retry receipt | One unique offered task; repeated receipt_id and second terminal transition rejected |
| Transient startup [0,3] | 1/3 verified; {t1,t2} censored; occupancy average 5/3, while offered-rate × completed-sojourn is 2 and verified-rate × completed-sojourn is 2/3; window is not steady-state eligible |
| Stable periodic [0,6] | 3/3 verified; occupancy average 1/2, verified rate 1/2, mean sojourn 1; finite identity holds exactly |

The law check is intentionally a diagnostic for the declared stable toy only.
The transient mismatch is expected and retained, not repaired by changing
the denominator. Candidate JSON, auditor JSON, command receipts, freeze and
source are preserved in this directory.

## Execution boundary and next question

The requested OrbStack image inspection failed because containerd reported a
missing content blob (operation not supported). No container was started.
The deterministic one-process experiment ran under macOS arm64 CPython 3.14.5;
the exact interpreter hash and frozen source hashes are in FREEZE.json.

This result tests only the newly proposed #5855 accounting controls. It does
not establish a real shared-queue paradox or a live service effect. The
unresolved #59 same-episode threat/change → identity-bound release → fresh
eligible action → independently useful effect/recovery gate remains open and
requires its separately authorized matched live allocation.

## Reproduction

From this directory, using the frozen interpreter:

    python3 -B candidate.py   # one invocation, exit 0
    python3 -B audit.py       # one invocation after candidate exit 0, exit 0

The four construction tests were run before freezing:
python3 -B -m unittest -v test_audit (4/4). The output files above are the
first candidate and auditor results; do not rerun this allocation.
