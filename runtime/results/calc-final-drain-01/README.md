# Same-response final evaluation in actual Calc use

One assistant-driven Linux/X11 Calc session, seed 991074, used the composed
adapter to enter 111 and 499, observe the fully rendered format dialog, and
confirm Excel format. The last action first received saved-effect evidence;
the newly connected `drain_final` helper then performed one command-free read
with zero server wait. Independent success `[111,499]` arrived in that same
CLI/review response. No additional model/tool turn was needed to request it.

The final socket exchange took 0.783712 ms on the caller clock (excludes artifact
persistence). Transport deadline was 250 ms. This does not imply the whole task
became that much faster: one run, changed seed, no counterbalancing, no model
token accounting and no human baseline. Total socket exchanges before cleanup
remained eight; composition moved the final read inside the action call.

All three programs completed and verified empty input release. Explicit finish
closed the server with exit code 0. Saved workbook SHA256 matches independent
effect evidence. Final displayed pixels still showed the historical format
dialog; receipt success came from saved-file evaluation, not that image.

The raw report preserves early evidence, final request/reply, evaluated outcome
and combined records. This duplicates some evidence in the default receipt
view; presentation/token cost remains unmeasured. Pending or lost final reads
do not produce success and do not replay input. Tests also cover foreign result
identity and discontinuous final cursor. Twelve client/review tests passed on
Windows and WSL; live positive evidence is retained separately here.

`runtime/` contains original runtime evidence and workbook; `enter/`, `dialog/`,
`save/` contain all exchange artifacts, including `save/final-request.json` and
`save/final-reply.json`. The client snapshot reconstructs the live source by
reversing one subsequent selector change (`reply` to combined `result`): final
code chooses from all received records, so a later observation is not ignored.
The live tail contained only evaluation, so this change does not alter its image.
Frozen `drain_final.py` and runtime sources were not edited. Historical paths
remain unchanged. `SHA256.json` covers evidence before this README was added.
