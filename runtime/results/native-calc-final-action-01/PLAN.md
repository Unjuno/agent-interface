# Calc final-action transfer

H: the integrated explicit finish-after path works on a real Calc modal boundary,
with one fewer finish-only exchange and without automatically confirming a dialog.
T: one fresh private WSL/X11 Calc allocation, seed991103, text gap2ms, max stages4.
Primary assistant views initial sheet, uses keyboard-only entry of public A1/A2
values and Save without finish_after. It views the actual returned modal, chooses
the format-confirmation button from that image, and sends that final click with
finish_after=true. No helper model/sensor lanes. No input retry after an ambiguous
or failed dispatch; an unexpected view is retained and assessed before input.
D: freeze current main/source hashes before launch; retain requests, returned
images/metadata, programs, independent workbook score, release and cleanup. Audit
the workbook separately and link exact request/reply/image identities. Compare
request count with native-calc-explicit-task-01/run-2 (same seed and task).
C: PASS_SCOPED only for correct A1/A2 and B1 empty, two explicit requests (entry,
then viewed modal confirmation), final reply containing action/image/evaluation/
completed cleanup, neutral release and terminal owner. Preserve any failure or
STOP without replay. The prior three-request run remains unchanged. Additional
unexpected steps mean the two-request hypothesis is not established.
U: causal latency/token/quality benefit, all dialogs/apps and human-tempo. Image
is last reviewed pre-evaluation/pre-cleanup capture, not a post-close screenshot.
No engine/gameplay benchmark or new sensor research. Docker is not restarted.
