# Win32 custody visibility across launchers (D14)

The read-only Windows probe found a real split: the same unpackaged Python
interpreter and logon namespace read an existing custody journal when launched
under Codex, but saw neither that journal nor its initialization marker when
launched by desktop Explorer. This is **FAIL for cross-launcher continuity**.
The retained journal was clear, revision 358; no input was dispatched.

## Evidence and diagnosis

Baseline main: `38cd13e9ccfd8fc779337d470020513004bf2d48`.
Runtime candidate: `5634e92614464046ea18fbfb3803d91f71109c15`.
Interpreter: the same local CPython 3.14.2 executable in both contexts.

| Observation | Codex descendant | Verified desktop-Explorer descendant |
| --- | --- | --- |
| Process package identity | no package (15700) | no package (15700) |
| Logon namespace | equal | equal |
| Journal at logical LOCALAPPDATA path | present | absent |
| HKCU initialization marker | present | absent |
| Explicit retained physical journal | same file and bytes | same file and bytes |

The physical journal is under the launcher's package `LocalCache/Local` tree.
Handle final path, device/file identity and SHA-256 agreed; the hash remained
`e02af656eed97a12530fb97b10edcb5959a2bb6a30a00dea2186cbabc6383515`.
Before/after journal snapshots agreed in all six retained reports. The marker
has one observation per report; equality compares the pre-repair and
post-factory observations in each context, not a continuous registry trace.

An initial ordinary `Shell.Application` call saw the Codex view and did not
qualify a distinct Explorer context. The later launch obtained the desktop's
shell dispatch through `IShellWindows`, `IServiceProvider`, `IShellBrowser`
and its background folder view. The child's bounded ancestor chain matched
the desktop window's Explorer PID, with consistent creation times.
[Microsoft documents this desktop-shell launch pattern](https://learn.microsoft.com/en-us/windows/win32/shell/samples-execinexplorer).
Package identity is therefore not sufficient evidence of shared store
visibility on this host. The observed AppData/HKCU difference is consistent
with [MSIX virtualization](https://learn.microsoft.com/en-us/windows/msix/desktop/desktop-to-uwp-behind-the-scenes).

## Scoped repair and validation

The native factory now checks an empty view for the same namespace's retained
journal in the known MSIX `Packages/*/LocalCache/Local` layout. A peer, an
unreadable inventory or an exceeded entry bound prevents first use. Clear
peers also block initialization because their retired-generation history
must not disappear. The check runs before native state construction and is
repeated under the existing namespace mutex immediately before initialization.
Existing-state polling does not traverse package directories.

The new regression failed on the baseline for both clear and unresolved peer
journals: an empty local view incorrectly initialized. The repaired custody
suite passed 29 tests. Seven related caller, custody, helper and guarded-input
suites passed **202 tests normally and 202 under `-O`** (32.345 s / 33.680 s).
Tests also cover a peer appearing after factory construction, checking under
the mutex, unchanged peer bytes, namespace isolation, inventory failures and
the existing-journal path.

A fresh read-only native check exercised the repaired factory in each launch
context, replacing only its final constructor with a recording sentinel.
Codex reached the sentinel for its existing journal. Explorer raised
`CUSTODY_FENCE_PEER_STORE_PRESENT` before reaching it. No real fence, input,
ACL update, marker or journal write was performed by that check. This is
**PASS for the demonstrated empty-view refusal**, not input/recovery evidence.

## Custody and remaining work

Conditions, scripts, raw reports, hashes, audits and first failures are in
the task-local private packet `custody_launcher_continuity_20261112_d14`.
The initial composed test command had three wrong module paths; its import
errors are retained and excluded from the corrected suite counts. Early COM
construction errors occurred before any launch. The v3 probe inherited an
incorrect `custody_factory_invoked=false` metadata field: the native factory
did run, while `factory.real_constructor_invoked=false` is accurate. The
additive audit records this correction without changing original reports.

This repair does not migrate storage, reconcile already-divergent journals,
detect every virtualizer or establish a common authoritative store. It also
does not make an old runtime participate in the new check. Those boundaries
remain open. Before allowing arbitrary launcher transitions, qualify a
shared store and a migration that preserves unresolved custody and retired
generations. MAP01 completion, arbitrary late input and
[#57 same-model/all-attempt efficiency](https://github.com/Unjuno/agent-interface/issues/57)
remain separate goals.
