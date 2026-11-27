# MAP01 public-caller expiry attempt R270

**Disposition: `FAIL_PRESTART_DEADLINE_CROSSED`; source action remains `UNKNOWN`.** R270 froze exact current main `4d590fd6b31bdfaf20954e32b308ad96fba29a56`, with a 30 s authority lease and a 60 s delayed-operation wait. The public dispatch was pending. The producer start call took 30.031 s and returned 47 ms after the authority deadline; all 11 program operations were still `not_started`, with zero program actions, zero SendInput returns, and zero local cursor actions.

The public cancellation request arrived exactly at expiry and returned in 16 ms, within the frozen 250 ms grace. This shows the caller route was timely, but the task path never reached an authorized input start. The failure is a start-gate boundary, not a release-latency or task-effect sample. R270's source action stays `UNKNOWN` (`input_dispatched=null`, release unconfirmed, `task_success=null`, replay denied).

A fresh supervised session handled custody as distinct recovery attempt R272. It independently observed the producer absent, matched the durable `identity_verified` start gate and input obligations, and returned `not_dispatched`. Persistent custody is clear at revision 1000, the source generation is fenced, and LEFT/W/SHIFT readbacks are all up. The recovery result does not upgrade the source action or confirm physical release.

After R272, a separate Computer Use attempt to close GZDoom was followed by a 50→49 HUD observation while the app remained open. That event is not linked to an Unjuno operation or R270 receipt and is excluded from R270 effect evidence. A later process check found GZDoom absent, custody still clear at revision 1000, and LEFT/W/SHIFT up; no force termination was used, and the exit code is unknown. The local packet records this UI interaction separately; the screenshot bytes were not saved there.

The private raw packet contains 77 files / 10,661,597 bytes; manifest SHA-256 is `4b330e38fc926ce1b2168a7c793f4f6b3c9d3b34273aaacb324b6b7f46e4fe12`, independently verified. Conditions SHA-256 is `8dfc549752d21659baea4e4ced4e42100511ef0b49ac64dbe15331251d95b320`.

This is not a matched automatic/caller comparison and has no task-effect, model/provider, token, or efficiency result. It identifies a concrete integration boundary: producer startup can consume the entire 30 s lease before the public caller reaches an action. Issue #57 remains open.
