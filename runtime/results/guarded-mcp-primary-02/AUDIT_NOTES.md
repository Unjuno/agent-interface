# Initial audit outcome and correction

The first bundle audit exited 1 with `review receipt persisted after Save request`.
Inspection found equal filesystem timestamps for review/request pairs 5/6, 20/21
and 28/29; the other pairs had a roughly 4 ms positive separation. No review file
had a timestamp later than its Save request.

The initial audit incorrectly treated strict filesystem mtime inequality as
necessary evidence of sequential awaited host calls. The revised audit checks
only non-later coarse timestamp consistency and expressly does not prove strict
order from mtimes. Source/call/image hashes and independent saved values remain
mandatory and unchanged. The host calls in the primary conversation awaited the
explicit review write before sending Save; the retained files alone are weaker
than a separately retained ordered host event stream. This limit must remain in
any interpretation of this bundle. No existing raw file or review was rewritten.