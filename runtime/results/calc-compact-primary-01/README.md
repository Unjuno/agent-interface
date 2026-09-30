# Primary Calc use with compact public observations

On 2026-09-28 the primary assistant completed a fresh LibreOffice Calc task
(seed 991351) through the persistent public MCP archive and instrumented Node
relay on private WSL/Xvfb/Openbox. The task was A1=336, A2=439, saved as XLSX.
It used `compact=true, report_refs=true` consistently on ordinary observe and
dispatch requests. No helper model or scripted policy selected task actions.

The assistant reviewed a blank A1-selected sheet, entered the two values,
reviewed both values, requested Save, and saw the Confirm File Format dialog.
It inspected the focused client, explicitly selected the matching transient
dialog with a one-use review ID, reviewed the bundled screenshot, and pressed
Enter on the visibly focused Use Excel 2007-365 Format button. A subsequent
inspection with full-screen capture showed the main sheet, matching values and
no format dialog. The assistant then closed the connection. Only afterward,
the fixture read the saved XLSX; A1/A2 were independently verified as 336/439.

Eight MCP calls: observe, input, Save, inspect modal, review modal with capture,
accept format, inspect main with capture, close. Five images were delivered.
All three input programs completed with verified empty release. The relay exited
0. Fixture cleanup reaped Xvfb/Openbox/LibreOffice with -9/1/255 respectively;
this was forced fixture cleanup after saving, not normal application shutdown.
No recovery fault was injected in this trial.

## What this establishes and what remains awkward

The existing lossless v3 receipt projection can be consumed during an ordinary
desktop task including an explicit modal transition. Full reports remain inside
the same response and image blocks remain usable. The trial is a small usability
check, not a matched latency/token comparison or broad desktop reliability result.
The 20ms character gaps and explicit 100ms waits are per-program choices, not
redraw acknowledgements or a new wait default. Caller observation sequence and
prior relay return +120s admission lease remain caller assertions.

The final screen capture has the old configured dialog native_window_id, while
inspection evidence identifies the currently focused main window. Screen capture
metadata describes its configured target; it does not implicitly rebind to the
focused client. No further input was sent, so a main-window selection was not
needed before close. Callers continuing input must explicitly review/select the
main window. The focused main-window metadata title was empty even though the
visible title bar was readable; identity was assessed with the original window
ID, transient family and screenshot, not a title-only assumption.

The current tool flow still needs an inspection then a separate explicit review
for modal selection. This trial does not authorize automatic focus/selection or
prove those checks removable. It identifies a remaining source of decision
roundtrips for future integration work.

## Retained identity and checks

Trial main was `52d4ff221` (full source identity in allocation.json). The exercised
portable runtime was built from `6c34107a22af77e3f30f9c1db24ccba307721571`, SHA-256
`7962f327fad5d9ca63273c059e23c98186cdc7713766431f6d0418e97c987591`.
Archive/build metadata, fixture and relay sources, requests/replies, images,
seven reply-bound review notes, saved XLSX, evaluator output and cleanup are
retained. No files from earlier trials were overwritten.

Run `python3 -O runtime/results/calc-compact-primary-01/verify.py`. The read-only
verifier checks archive identity, call order, explicit v3 options, image delivery,
review bindings, input release, revision transition, saved worksheet XML and
process exits. It does not interpret screenshot pixels or treat presentation
callback time as first useful feedback. Actual model tokens/cost remain unmeasured.
