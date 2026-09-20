# Primary Calc relay use: observed input loss and explicit correction

One persistent relay connection carried startup, four explicit stage submissions
and final status. The primary assistant viewed the returned images and public
goal A1=300/A2=758, entered the values and saved. The format dialog was observed
before choosing its Excel-format button. After confirmation, A1 visibly showed
30 rather than 300; A2 showed 758. Initial input completion did not prove task
success. Both images and the original request remain retained.

The primary then selected A1 with Ctrl+Home, entered 3, 0, 0 as separate text
operations with explicit 20ms inter-character waits, and saved again. A fresh
image showed 300/758. An explicit fourth-stage finish evaluated the workbook
and closed the allocation. Independent openpyxl inspection confirms A1=300,
A2=758 and B1 empty. Three input programs released all keys/buttons. Owner
18237 returned terminal/code 0; EOF closed relay exec 82262 with code 0.

This deviated from the two-action plan: one corrective action and a separate
finish were required. The initial incorrect value is supported by retained
screenshots, not an intermediate saved-workbook snapshot. The exact cause of
the missing repeated zero is unproven; explicit pacing succeeded in this case
but is not a controlled minimum-delay or general reliability result. Do not
silently make 20ms the shared default from this single correction.

Run `python3 runtime/results/native-mcp-relay-calc-01/audit.py` with openpyxl.
It checks the manifest, image bytes, four request/reply hashes, input release,
final workbook values and terminal owner. PLAN.md precedes allocation; the
manifest predates this README and audit script. Production source is recorded
in provenance.json. No sensor development, autonomous replay or token/speed
claim is part of this trial. Response-file reads and primary decisions remain.
