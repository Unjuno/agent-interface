# A11 first private GUI drift result

Allocation `5260-a11-wslc-private-gui-drift01-20261004` consumed once.
Prospective Issue #5260 comment5972429398 and resource #5085 comment5972429549.
Executed source commit `0ce78633af09c89ee959903cc0e120393f4553b6`.
FREEZE SHA256 `8b134d0a0cca8336c0c08e566291f83a7de9db41e0c805ba00b54771ff1b8a9e`.
Candidate and auditor used that same clean source; no repair or replay occurred.

Candidate 2026-10-03T18:56:50.266636+00:00 through
18:57:01.414972+00:00, exit0, wall11.1462646s, six app exits0 and empty stderr.
Independent auditor 18:57:17.855642+00:00 through18:57:18.455614+00:00,
exit0, wall0.5989833s. First result METHOD_PASS_FINITE_FIXTURE_ONLY,
H_PASS_FINITE_FIXTURE_ONLY, errors=[]; retained stdout is authoritative.

| Arm | n | Target | Decoy | Saved target | Key / Save per row |
| --- | --- | --- | --- | --- | --- |
| STABLE | 2 | hxy | empty | hxy | 3 / 1 |
| DRIFT_STALE_CONTROL | 2 | empty | hxy | empty string | 3 / 1 |
| DRIFT_REFUSE | 2 | empty | empty | null (not saved) | 0 / 0 |

All six initially admitted a fresh target receipt. Both drift arms observed
bound target FocusOut then decoy FocusIn after the one decoy intervention.
The stale control's initial admission remained the same historical object,
but all three keypresses went to the decoy; clicking Save saved the empty
target. This is NOT task success. Refusal prevented emission in its two rows.
Actual shuffled row order: REFUSE, STALE, STALE, STABLE, STABLE, REFUSE.

Raw SHA256 `803279bfca0324b7a84b3a8d9458e261adc2257d8865f1229466f4d5826c47bc`.
Original audit stdout SHA256
`3bf58fa281900d4eff9c0525c4b31c2317aed00ab14fa55669e1d0625ce91ad3`.
Both original host stderr streams retained (swap warning), SHA256
`2562006e62622bcf41c809d627cdc2c6250516b8cf1c9ccd28072c331fcc4096`.
Retained contains38 byte-copied raw/files/logs/first launch receipts. Original
outside-repository run directories remain preserved separately. No provenance
claim is based on PowerShell's timezone-reformatted JSON; originals stay bytes.

Scope: six private instrumented Tk apps with deliberate focus intervention,
not naturally occurring drift, public focus sensor, physical key release,
atomic focus/key authority, reliability estimate, same-model heldout recovery,
human tempo, memory/performance benefit or production runtime adoption.
The inspector observation field `admitted` denotes final emission eligibility,
not absence of INITIAL admission in the refusal arm. Inspect the retained
initial gate and post_admission separately. Original A09/A10 remain unchanged.

Fresh post-role WSLc ps showed no running container. Owned --rm roles ended;
three older other-owner exited containers were untouched. Scoped CPU use is
released. Remaining delivery work: saved-packet corruption qualification,
manifest/local CI, batch remote push and reviewable PR/main integration.
