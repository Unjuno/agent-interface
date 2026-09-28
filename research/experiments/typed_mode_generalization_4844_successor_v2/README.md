# Issue #5184 — fresh-seed typed-mode replication

Status at intake: `CONSTRUCTION_PASS_FORMAL_NOT_STARTED`.

This additive v2 successor preserves #4844/#4863/#4155/#4169 and the #5184 -01 pre-freeze seed-exposure STOP. It uses only fresh allocation `typed-mode-4844-successor-20260928-02`, seeds 484421/484422, and a separate path. No predecessor source/result is modified or run for this allocation.

The committed [plan](PLAN.md) records H/T/D/C/U, outcome gates, container policy and commands. [FREEZE.json](FREEZE.json) binds exact source/test/auditor bytes, current-main intake, the cached Docker Desktop image, and formal command contract. Formal seeds must not be generated until the freeze commit and issue record have been verified.

Construction so far: CPython host syntax checks passed; alternate-seed-only test passed; the same construction test passed in Docker Desktop using the exact pinned image, `desktop-linux`, no network, read-only root/source, and 1 CPU / 512 MiB / 32 PIDs. The construction test temporarily substitutes seeds 59001/59002 and checks deterministic output, 4,800 rows, equal block/mode balance and mapped labels. It does not produce or inspect formal-seed results.

Formal runner has not been launched. No efficacy or scientific result is claimed. The intended formal sequence is one offline Docker runner followed, only after successful completion, by one distinct offline raw-only auditor container. The formal disposition and all raw records, commands, hashes, exits and receipts will be appended after execution; no retry is permitted.

Scope remains synthetic only: no real GUI diagnosis, cross-app transfer, runtime integration/authority, safety proof, model quality, latency/token efficiency, human tempo or product claim.
