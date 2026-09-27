# Primary mixed-app use of caller-owned public dispatch

Source: 60f3e9a0d2a4a221c00e12d3be0977e6c772e957; fresh seed 991294.
This checks the #4683 integration across Inkscape, Calc and the format dialog,
rather than only a single Calc document. The primary used one real MCP SDK client,
viewed the initial image and every returned action image, and chose each action.
No helper model, sensor, input replay or separate observation request was used.

The first click at the red rectangle center [619,391] was refused before input:
visually_flat_source_region. The returned image supplied source 2; the primary
chose [598,390] inside the same rectangle near its border. That explicit correction
succeeded. Preserve the failed first request: it adds one refusal/recovery round
trip. This is not a no-refusal run or a stale-state test.

Four public dispatch reports completed: select/move/save Inkscape, switch to
Calc, enter/save cells, and confirm the format dialog. All contain verified empty
input releases. The saved SVG has rectangle x=54,y=50,width=40,height=30 and no
transform; XLSX has A1=748,A2=745. Finish evaluation succeeded and native_status
recorded owner PID 67935 exit 0. The managed client exited 0 (terminal observation).
Descendant exit verification remains false and is not claimed.

There were five action decisions (one refused, four executed), then finish and
status, plus initial start. Post-action waits remain 250/300/250/250 ms.
The archive retains calls, images, receipts and SDK timings; SDK timings do not
measure model interpretation or first-useful-feedback recognition.

The resulting tool-description change advises choosing an intended target with a
distinctive local patch and explains explicit correction after a no-input refusal.
The live run predates that description change. Its performance benefit is untested.
This is scoped mixed-app evidence, not the matched six-task acceptance matrix,
human-tempo parity or token/cost savings. Overall integration remains incomplete.

Run python3 verify.py here for archive integrity, both saved effects, four public
reports/releases, the initial no-input refusal and owner exit. No UI is replayed.
