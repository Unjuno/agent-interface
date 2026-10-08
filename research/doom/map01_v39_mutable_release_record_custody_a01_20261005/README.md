# Mutable owner-release record custody A01

This package tests the unarchived mutable-record custody diagnostic reported on Issue #59 and discussed on PR #7829. It is deliberately separate from the pending-expiry gap tested in PR #7830.

## Result

- A01 stopped before Docker launched because the first command placed an environment assignment where Docker expected the image reference. Container starts and candidate executions: 0. Exact command and CLI output are preserved in `STOP_A01.txt`.
- A02 used a fresh run ID and the pinned cached arm64 image. The frozen bridge V2 baseline reproduced the issue: while aggregate pointer verification was gated, bridge consumed an `owner_release` record with `verified=false` and one `PHYSICAL_SAMPLE_UNAVAILABLE` per-key measurement. After aggregate keymap sampling succeeded, the owner mutated that same record to verified-empty. A second bridge drain did not revisit the consumed record, leaving bridge-held F8 while owner and fake physical state were empty.
- The one-variable diagnostic neutral-state revisit cleared bridge-held F8 without duplicate receipt emission and without upgrading the unavailable per-key sample to `CONFIRMED_PHYSICAL_UP`.
- Independent raw-only audit: 2 cases, zero mismatches. One Docker candidate command invoked the matched baseline and probe once each. No retries.
- Auditor wrapper history: its first A02 audit wrote to the formal_01 path by mistake; the corrected formal_02 report is byte-identical. The candidate raw was never rerun or modified; see `AUDIT_WRAPPER_NOTE.txt`. A post-run no-overwrite preflight correctly refused the already occupied result path.

## H/T/D/C/U

See `PROTOCOL.md` for the frozen hypothesis, exact schedule, decision rule, source/image pins, and scope limitations. This is fake-Xlib scheduling evidence only. It does not establish physical keyboard state, live X11, application/game consumption, useful feedback, bounded recovery, threat control, or Issue #59 completion. The probe is diagnostic-only, not a production repair or recommendation to promote.

## Reproduction and integrity

The exact candidate source is retained in `research/doom/map01_v39_expiry_pending_owner_current_a03_20261005/candidate_source/` and bound in `SOURCE_LOCK.json`. Formal raw candidate/audit files and disposition are under `results/formal_02/`; A01 has no candidate output. See `COMMANDS.txt`. Local focused checks and their exact scope are summarized in `LOCAL_CI.md`. Verify package bytes from repository root with:

```sh
shasum -a 256 -c research/doom/map01_v39_mutable_release_record_custody_a01_20261005/SHA256SUMS.txt
```
