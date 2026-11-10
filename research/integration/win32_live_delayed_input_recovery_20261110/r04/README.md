# Win32 persistent custody ACL audit r04

Date: 2026-11-10 (Asia/Tokyo)
Source action: r03 operation `a691feb96ad84a25944ff7f3f174be3e`.

## Purpose and method

This read-only follow-up checked the actual current-logon custody journal used by r03 after the action had resolved. It read the journal JSON and Windows ACLs for the custody directory, its journal file, and the per-logon registry marker key. It made no state changes and did not issue input.

## Result

The journal was `clear`, `pending` was null, revision was 18, and `last_resolved` matched the r03 operation. The directory, journal file, and registry marker key each had a protected DACL with exactly the SYSTEM, local Administrators, and current-user principals. Machine-specific account names and the logon namespace digest are intentionally not included. See `audit.json` for the structured result and scope.

## Limits

This verifies the present ACL and custody state for this host logon after r03; it does not prove resistance to processes running as the same user or an administrator, nor access control on another profile or host. It does not prove that Windows cannot process an already accepted input after a finite observation horizon. The source action's task success remains unknown/null and replay remains denied.

`SHA256SUMS` covers the audit record and this README, excluding itself.
