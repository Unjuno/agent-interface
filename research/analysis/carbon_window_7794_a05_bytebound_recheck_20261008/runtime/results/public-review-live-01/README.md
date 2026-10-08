# Primary public review use and timing integration

One fresh Calc task used the portable runtime built from main
317071858f3bc9e0d3d90330095b90c9835dc591 (archive SHA-256
cb6b9032ac823ae971b4c46b178791e623658f2961683d14e0cab3fad4367782).
The primary assistant operated the public persistent MCP through the instrumented
relay, presented each returned image, and explicitly recorded nine v2 public
capture reviews. No helper model or sensor was used.

The first allocation (991353) failed before app launch: the private window-manager
probe did not become managed/viewable in the existing 3 s budget. No task input
was sent. A separate logged setup diagnostic succeeded in 2679.96 ms and retained
Xvfb/Openbox logs; this does not establish the cause or fix the timeout. The next
allocation (991354) was a separate fresh task, not a replacement of the failure.

## Task and failures retained

The goal was A1=804, A2=592, saved as XLSX. Fourteen public calls returned,
including three completed input programs, a preflight program refusal, an invalid
review argument request, and an expired target review. Nine images were presented
and explicitly reviewed. Input was not replayed after an ambiguous visual result.

The first post-input capture still appeared blank. Re-observation showed 804/592.
A Save program omitted its explicit focus operation and was refused before program
execution (the reported backend_emissions=16 was the previous cumulative total).
The corrected program emitted four events. Its immediate capture still showed the
prior sheet; target inspection then showed the format dialog. An assistant-side
argument-name error was refused without invocation. During correction the 30 s
review expired; a new inspection/review bound the modal at revision 2. Enter was
sent once. Final captures did not establish visible semantic completion, so the
primary review explicitly left that unproven.

After closing the MCP input session and relay, an independent workbook read
confirmed A1=804 and A2=592. The verifier also reads the stored XLSX XML directly.
All three accepted input programs and session close reported verified empty input.
The relay exited 0. Fixture cleanup forcibly reaped Xvfb, Openbox and LibreOffice
with return codes -9/-9/-9; this was not a normal application exit.
The public target inspector returned the corrected UTF-8 main title after the
modal closed. Screen-capture target metadata still named the selected old modal;
inspection did not implicitly rebind it.

## Integration defect found and repaired

The existing read-only host timing summarizer rejected the newly integrated v2
public review schema. The first failing invocation is retained. It now accepts
both declared schemas and requires explicit null source_sequence for public v2
receipts, including in the host event. A fabricated sequence remains rejected.
This preserves the existing attribution-only contract; the summarizer does not
independently certify capture validity, visual attention, or semantic success.
Nine focused tests cover legacy behavior, public timing, invented/missing sequences,
unknown schemas, corrupted identities/order and partial operations.

Run `python3 -O runtime/results/public-review-live-01/verify.py` for read-only
archive/hash, reply/image/review, saved-file and timeline verification. Raw records
include the failed setup, separate diagnostic, fresh trial, exact host modules,
portable build and local checks. No fixed wait, review timeout or input authority
was relaxed. The new task had additional observation and recovery round trips;
no speedup, human-tempo, actual model-token/cost or matched comparison is claimed.
