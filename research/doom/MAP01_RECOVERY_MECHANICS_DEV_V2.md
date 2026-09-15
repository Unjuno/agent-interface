# MAP01 recovery mechanics development v2

Status: **FROZEN REPAIR; NOT YET EXECUTED.**

Allocation: `map01-recovery-mechanics-dev-02`  
Base: `f34cd44f4c4c833638dbf2ae5911e322acfacd96`

Dev-01 remains a retained FAIL. Its raw recovery program did execute one `a` hold and cleanly release, but the development analyzer incorrectly filtered `input_admission` by program `id`. V13 admissions are bound by `intent_token`; only `accepted`/`keys_held`/terminal carry the program id.

V2 changes exactly one evidence rule: resolve `accepted.id -> intent_token`, then join `input_admission` and verified `input_release_transition` by that token (with release batch id equal to the program id). Wait window 600 ms, recovery hold 240 ms, health-loss guard 8, lease 1500 ms and all runtime/scorer mechanics remain unchanged. The fresh development seed is 990616 because dev-01 is consumed.

PASS criteria are unchanged: coast admissions 0; recovery admissions >=1; recovery lowers the 600 ms no-retained-input upper bound; both arms finish with empty release, zero scorer leak and zero missed scorer periods; both terminal-score audits pass. Independent gameplay outcomes are retained but are not efficacy evidence.

A PASS only closes the real-MAP01 mechanics/measurement integration for the bounded recovery primitive. The separately frozen formal recovery-v2 efficacy allocation still requires its own runner and lease.
