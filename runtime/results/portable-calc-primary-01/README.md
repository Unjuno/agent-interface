# Primary use of the portable public MCP with Calc

On 2026-09-21 the primary assistant used the packaged public MCP through a
persistent Python SDK connection on private WSL/Xvfb to create and save an invoice
sheet. The assistant viewed retained screenshots and authored each next request;
no additional model, subagent, sensor controller, or automatic input replay was used.

Source: `c3abca57cb9d0e5cfea49794e35b33a84337959f`.
Archive used: 159287 bytes, SHA-256
`4d3f9d1ec60b740e3c815f01eee978dae737c14a91e7a08a1af1c94d7d83b912`.
It was independently built in Windows and Linux with identical bytes. The public
MCP process ran from `/tmp`, outside the checkout, without repository PYTHONPATH.

## Observed result

The final screenshot displays Quantity / Unit price / Total, 12 / 9 / 108.
Independent inspection of saved `invoice.fods` finds the same headers and values,
with C2 formula `of:=[.A2]*[.B2]`. The last input dispatch reports completed,
verified input release, and no recovery required.

The successful allocation contains four explicit observations and three dispatch
requests: close the startup tip, a zero-emission formula-text refusal, and an
explicitly revised input batch. Two dispatches emit input and complete.

## Failures and interaction findings

- Allocation 01 directly launched `soffice.bin`, which exited with code 81 before
  any MCP connection or input. Its process log, initial document and cleanup are
  preserved. The exact initialization cause is not established by that exit code.
- Allocation 02 used the normal `libreoffice` wrapper but the harness failed to
  locate its task window within the bound. No MCP/input was issued. All captured
  process-group members were absent after cleanup.
- Allocation 03 additionally read `_NET_WM_NAME` and lengthened the startup bound.
  It located the window; these changes were not independently compared, so this
  does not prove which change resolved allocation 02.
- Two window-client observations showed a black central region. An explicit
  screen-physical observation of the private display revealed the overlapping
  Tip of the Day dialog. The assistant clicked its visible OK button. Window
  capture alone had not supplied the information needed for that decision.
- A batch containing text `=A2*B2` was refused before all input with
  `unsupported text character U+003D` and `backend_emissions: 0`. The primary
  assistant deliberately authored a new batch using the supported `equal` key,
  text `A2`, explicit `SHIFT`+`8`, and text `B2`. This is a layout-specific recovery,
  not a proposed general text implementation or an automatic replay policy.
- The input dispatch's screenshot still showed partial editing and a saving
  indicator. A later explicit observation showed the completed sheet. Fixed
  `wait_update: 50` was not sufficient evidence of semantic completion.

## Retention and scope

`evidence.tar.gz` retains all 75 files from the three distinct allocation
directories, including harness sources, decisions, actual requests with leases,
MCP replies, PNGs, raw reports, source/final documents and process logs.
`manifest.json` lists their exact byte counts and SHA-256 values; all archive
members were reread and checked. No failed allocation was overwritten or relaunched.

Allocation 03's tracked processes were reaped; captured group-member paths were
absent after cleanup. The harness still explicitly reports
`descendants_verified: false`: this is not proof of exhaustive descendant closure.
The owner command completed with exit 0. The six-request decision bound ended
the owner after the final observation.

Source/binding values remain caller assertions. The private harness assigned a
10-second host-monotonic lease only after reading each explicit primary decision;
the public MCP did not mint authority. This was saved-file/view-tool delivery,
not the newly configured direct host MCP route. No host-presentation acknowledgement,
matched comparison, model-token/cost record, human-tempo measurement, or formal
container acceptance is claimed. Keep the broader #3352/#3370 gates open.
