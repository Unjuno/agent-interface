# Primary use of explicit target-review requests

Portable source: 4fae79b87a835028633268f54028dcb101617eb6
Archive SHA-256: 078568c3aa4528f316f01597a67d8daf7fe10282f1e6435a8ebff8adf6d7810f
Fresh private Calc allocation: 991355, goal A1=442 / A2=351, save XLSX.

The primary assistant made nine public MCP calls and seven image reviews using
the instrumented persistent relay. The third call showed the format dialog.
Call 4 inspected it with a screen capture. After viewing that evidence, the primary
passed its review_request.tool and review_request.arguments unchanged as call 5.
The target was selected at revision 2 with matched capture consistency, then Enter
was sent once to accept Excel format. The first post-save capture was transitional;
a further read-only inspection showed both values, an enabled sheet, and no dialog.
Unused main-window candidate requests from calls 7/8 were not executed.

The independent saved-workbook read found 442 and 351; the retained verifier also
reads the XLSX XML without invoking Calc. Three input programs completed with
verified empty release; input session close was verified empty; relay exit was 0.
Fixture process cleanup returned Xvfb/Openbox/LibreOffice codes 0/1/255, not normal
application exit evidence. The primary made no helper-model calls or sensor.

No argument-name error, expired target review, or automatic request execution
occurred in this task. This is one engineering-use case, not a success-rate or
speedup estimate. The previous 991354 task had 14 calls and caller mistakes;
different seed/values, rendering load and caller practice prevent attributing the
9-versus-14 difference to this feature. Fixed waits and review lifetime were not
changed. Caller observation sequence and 120-second input lease assertions remain
caller-provided; they are not freshness certificates or server-issued authority.

The candidate request costs 1335 additional UTF-8 response text bytes
across three inspections, measured by removing only the two new fields from the
same retained JSON serialization. This is a byte cost, not actual model tokens or
money. The unchanged image blocks are not included in that comparison.

Validation: 276 protocol + 126 harness checks pass. Tests submit returned requests
through the actual public MCP schema (with/without capture), retain historical
requests without renewal, reject changed/expired/tampered evidence and withhold
requests on capture failure/disagreement. Neither inspection nor selection sends
input or clears recovery. Read-only verifier checks exact replies, image/review
hashes, selected request equality, saved XML, scope cost and the host timeline.

Run python3 -O runtime/results/target-review-request-primary-01/verify.py.
