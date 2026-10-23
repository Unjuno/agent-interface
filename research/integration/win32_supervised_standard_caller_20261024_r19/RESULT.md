# R19 result

R19 used one public stdio-MCP dispatch and cancel with a 4-second retained
injected Q-down callback on the user-authorized Windows PC. Cancel returned in
1.684 ms. The exact producer identity was observed exited at the second sample
(232 ms after cancel) and remained exited in later samples. During the retained
callback, 65 same-call polls showed action `running`; cancellation changed from
`pending` to `unknown` at 2865.8 ms after cancel. Every poll kept
`release_confirmed=false` and `replay_allowed=false`; task success remained
null. Thus cancellation uncertainty became visible within the 3500 ms bound,
but the action itself stayed `running` and no release was proven.

The callback returned at about 4061 ms after cancel and the probe suppressed the
held Q-down. The exact R19 click/text/save effect was independently observed.
The fixture exited, its window disappeared, the hook thread exited, and the
previous foreground window was restored. Public `interface_close` remained
`busy` with cleanup `UNKNOWN` across 37 bounded attempts; this does not count as
a clean public-session close. The frozen audit reports `FAIL_OR_UNKNOWN` (6/9).
Two audit checks miss direct evidence: the producer-exit check reads a null
top-level callback-return field although the event row records the callback
return after the exited samples, and the suppression check reads a pre-release
top-level snapshot although the event row records `suppressed=true`. A third
check correctly exposes the unresolved action state by requiring action
`unknown` in addition to cancellation `unknown`. Keep that audit immutable; the
raw polls and event trace carry the direct evidence. R19 demonstrates bounded
fail-closed cancellation status only, not a terminal action, input release,
recovery, MAP01, or WSLc behavior. Do not repeat this one-shot attempt.
