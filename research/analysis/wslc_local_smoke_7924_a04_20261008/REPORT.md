# A04 report — receipt-shape preflight passed; formal audit failed

## Result

FAIL_AUDITOR_CONTRACT. The separate pre-freeze WSLc shape smoke passed and verified the actual A02 candidate (absence_verified at top level) and auditor (targeted_inspect_checks[1].absence_verified) cleanup records. The one frozen formal A04 WSLc auditor invocation then exited 1 in validate_frozen_a04, before any A02 baseline validation, with KeyError: 'cid'. A04 expected the preflight receipt field cid, while the retained PREFLIGHT_RECEIPT.json records container_id.

Thus A04 does not establish an independent audit of A02. No AUDIT.json was produced. The formal run used the pinned cached Python image, WSLc 3.0.1.0, --network none, a read-only package mount, --pull never, --rm, one CPU, and requested 512M. WSLc warned that cgroup/swap limits were unavailable; no hard memory-limit claim follows. The exact formal CID was inspected once and was absent after auto-remove.

## Preservation and non-actions

- A02 and A03 files, branches, PRs, and FAIL_AUDITOR_CONTRACT outcomes remain unchanged.
- The successful A04 preflight receipt-shape smoke and the failed formal A04 invocation are distinct retained events.
- No candidate, A02 auditor, or A03 auditor ran again. The formal A04 auditor was not retried. No Docker action, image pull, global container list, or unrelated lifecycle operation occurred.

## Scope

No Docker parity, speed, memory-relief, hard-limit, OOM-prevention, GUI/model, or general migration claim.
