# Issue5442: owned browser form to SQLite endpoint

Eight actual DOM form submissions all returned HTTP200 and visibly showed
`Dispatcher accepted`. A different Python process using a fresh read-only SQLite
connection confirmed only C001/C005. The six seeded wrong-target, no-op and
stale-precondition effects remained UNKNOWN. Each received exactly one new
fresh-version repair submission; all six repair effects were CONFIRMED. The
original initial decisions remain unchanged.

Result: **PASS_APPLICATION_ENDPOINT_SCOPED**. This is a controlled application
construction, not a general GUI success rate or a promoted runtime authority.
The separate raw-only auditor reconciled14 operations, their SQL backups,
56 UI trace entries and14 HTTP POST200 records; ten copied-raw mutations were
refused, including actual event target and the integer/boolean alias.

| Cases | Seeded endpoint behavior | Initial A/B effect | Initial decision | New repair |
|---|---|---|---|---|
| C001/C005 | correct target and preversion | A0→1, desired value; B0 empty | CONFIRMED | not needed |
| C002/C006 | actual target B | A0 empty; B0→1, desired value | UNKNOWN | A0→1 desired; B1→2 empty |
| C003/C007 | no-op | A/B0 empty | UNKNOWN | A0→1 desired; B0 empty |
| C004/C008 | precondition changed before write | A1→2 desired; B0 empty | UNKNOWN | A2→3 desired; B0 empty |

## Evidence and first outcomes

The source freeze SHA256 is
`3d79ff351af775bda98bbaab5247010edb1e9936b9419146539f610c88baa11f`.
It preceded the sole primary server startup at2026-10-03T03:21:03Z. This study
used CPython3.11.9 / SQLite3.45.1 / Windows with one owned hidden Codex IAB tab,
DOM locators through CUA only. No repository runtime, external site, additional
worker, native desktop input, container or experimental model API was invoked.
Browser graphics and coordinating assistant settings are unmeasured.

The package retains original source bytes under `retained-source/`; `.py`/`.js`
files have an added `.txt` extension to avoid automatic execution. Source names
in the original FREEZE.json are unchanged. `SOURCE_MAP.json` maps them to these
plain-text files. To inspect the pure auditor, materialize all original names
plus FREEZE.json in a new private directory and run auditor.py against the
retained run-01. This reads retained data and does not start the app or repeat
GUI operations. No original allocation is available for a primary replay.

`run-01/` retains the first observations, prestate, coherent SQL backups, final
database, UI traces, initial/final JPEGs, source-load binding, process identity,
stdout/stderr, command exit receipts and resource cleanup. SHA-256 identifies
bytes, not authenticity. The endpoint is authored by this worker; distinct
process/connection observation is not independent observer trust.

First construction failed compilation because two multiline return expressions
lacked parentheses. `construction-01/` preserves the original app source,
compiler error and first failure. Ordinary construction repair added those
parentheses. `construction-02/` then passed8 seeded cases,8 duplicate guards,
6 stale repair guards and6 fresh repair checks before the source freeze, with
zero GUI actions/primary server starts. These unit checks are not GUI evidence.

First CUA actor setup rejected eval (`Code generation from strings disallowed`).
That occurred before goto or any submit. The literal async function was then
defined through CUA and compared to the frozen actor source text, changing only
the loading method. Both records remain. The actor and primary app source were
not edited after freeze, and no primary operation was retried.

After all fourteen completed operations, read-only observation/backup and proof
capture, the owned tab was closed. The exact server PID and command line were
checked before Stop-Process; its observed exit was-1 (intentional termination,
not a graceful-shutdown claim). The launch observer itself exited0. No shared
input/display lease or main apply lock was held.

## Decision and limits

H/T/D/C/U and the prospective sequence are preserved in PLAN.md and
UI_PROTOCOL.md; the Japanese variable/type/unit table is VARIABLES.md, all in
retained-source. The initial-only dispatch baseline yields eight accepted
returns despite six seeded semantic failures. Final text alone would also miss
the stale-precondition cases. The binding predicate adds target/preversion and
actual saved state; bounded repair establishes a new explicitly different
intent using a guarded SQL transaction.

This advances T8's fixture-only boundary to an actual controlled HTML form and
committed SQLite state visible to another connection. It does not establish
arbitrary application fidelity, observer authenticity, multi-user/concurrent
safety, crash/power-loss durability, physical input occupancy/release,
latency-matched efficacy, model/resource savings or production kernel adoption.
T7/T8 source/raw/allocations/conclusions remain unchanged. Issue5442 stays open.

Only this additive non-executing package is proposed. Source freeze main was
6da2b492b9c2a9d76e5c54d35a0ae50b7b49edde; publication base is recorded separately.
Content votes, current-main nonauthor combination, actual GitHub requirements
and one conditional history-preserving application remain separate. No main
write is claimed.
