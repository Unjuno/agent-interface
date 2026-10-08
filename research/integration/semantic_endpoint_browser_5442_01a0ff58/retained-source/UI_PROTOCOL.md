# Prospective owned-browser protocol

All browser interactions use mcp__cua_repl and the existing semanticTab binding
(owned IAB browser2/tab1). Ordinary Node file I/O writes the trace and reads this
actor source only; it never queries endpoint data, HTTP, other tabs or a browser
control library. eval of actor.js defines functions; invocation uses CUA only.

1. Freeze app/observer/auditor/actor/scenarios/plan/protocol and variables.
2. Start one stdlib loopback process in run-01, preserve PID/port/stdout/stderr.
   No primary restart/reset/replay. Record initial empty SQL state before any GET.
3. Initialize trace once with exclusive file creation. Load actor.js once.
4. Navigate the owned tab to the server root. Observe a fresh full DOM snapshot.
5. From dashboard invoke runEndpointTrial for C001..C008, in that order, passing
   only trial ID, desired text and initial phase. Each function observes editor,
   fills New value, observes intent, records nonce before exactly one Save,
   observes Request processed/Dispatcher accepted, then returns/observes dashboard.
   A consumed key is registered before submit; any unexpected result stops this
   primary operation. No blind retry or source change after freeze.
6. Run observer.py --phase initial once in a different Python process; preserve
   raw rows and coherent SQLite backup. Initial decisions are permanent.
7. Reload dashboard once so it shows observer decisions and Repair Cxxx links.
   For six UNKNOWN rooms only (C002/3/4/6/7/8), invoke the same frozen actor with
   phase repair. Each editor is freshly loaded and displays A/B values/versions.
   Its version-bearing form authorizes one atomic comparison/restore/write on
   fixture-owned rows only. No repair for C001/5. Max one repair per failed room.
8. Run observer.py --phase repair once; save its independent SQL backup. Run the
   separate raw-only auditor on immutable raw/backup/trace (not app simulation).
9. Reload root for final proof screenshot, save JPEG to outputs and research raw.
   Preserve all first outcomes, including construction SyntaxError. Stop only
   the identified owned server, record process exit, and close only owned tab.

Source preflight/ordinary unit repairs are allowed before this source freeze.
If a GUI submit becomes uncertain, save partial evidence and HOLD this unit;
do not treat an HTTP response, missing exception, or actor return as endpoint
success. No latency/call-efficiency comparison is performed.
