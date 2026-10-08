# Issue #5189 — fresh-seed typed-mode replication

Status: `CONSTRUCTION_PASS_FORMAL_NOT_STARTED`.

This v3 allocation follows the preserved #5184/#5188 Docker launch STOPs; it does not reopen or modify them. Formal seeds 484431/484432 are unique to allocation `typed-mode-4844-successor-20260928-03`. The previous #5184 allocation seeds are retired. Evidence goes only under `research/experiments/typed_mode_generalization_4844_successor_v3/`.

The [plan](PLAN.md) sets H/T/D/C/U, exact analysis, decision rules, offline Docker Desktop commands, and limits. `FREEZE.json` binds exact Git blobs/SHA/size, image identity and command contract before any formal data is generated. The local `.gitattributes` disables line-ending conversion within this evidence directory. Construction test history, including the corrected auditor block-set defect, is in [CONSTRUCTION.md](CONSTRUCTION.md).

Construction used only seeds 59003/59004. CPython host syntax/unit checks passed; the same test passed in Docker Desktop on `desktop-linux` with the exact cached image, network disabled, read-only root/source, one CPU, 512 MiB and 32 PIDs. The independent auditor verified alternate-seed rows, rejected 16 directed corruptions, and refused noncanonical JSON and duplicate keys. Construction data is excluded from formal estimates.

No formal runner has started and no scientific result is claimed. The intended sequence is one offline Docker Desktop runner followed—only after successful completion—by one separate raw-only auditor. Any source/image/process/evidence/audit STOP is retained without retry.

This synthetic study does not establish real GUI diagnosis, transfer, runtime integration/authority, safety, model quality, latency/token efficiency, human tempo or product readiness.
