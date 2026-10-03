# Issue 49: declared edit offsets through native X11 replacement

Worker 01a0ff51-d447-7cb3-bb02-36d7e1d30b28, FINAL-v5. This is an
additive research-only adapter experiment, not a production EditContext API.

H: In Qt5/X11 controlled text, passing Unicode-scalar offsets directly as
QTextCursor numeric positions can replace a different range after supplementary
characters. Standard explicit scalar-to-UTF16 conversion, or declared native
UTF16, plus exact synthetic source binding suffices for the selected cases.
Unknown units and staged stale content must yield before native input.

T: Eight predetermined cases, two widgets (QPlainTextEdit/QTextEdit share Qt's
text engine), untyped then typed arms; 32 fresh app/Xvfb cells. S01 ASCII,
S02 supplementary prefix/backward selection, S03 ZWJ prefix, S04 flag prefix,
S05 decomposed accent prefix, S06 staged stale source, S07 unknown unit,
S08 already-native UTF16. Initial text and numeric selection are fixture setup
through Qt APIs; after selection the only replacement is unchanged main
X11Backend's actual XTEST text X, admitted by unchanged core contract, ending
in release/readback. The research-controlled fixture lease and sequence values
are not an external live authority validation. No post-ready text insertion API.
The controller explicitly receives synthetic current text for binding. Saved
UTF8/state/journal/PNG are retained. Scorer imports no producer/runtime/policy.
Both arms receive the same exact saved-effect oracle after input. This stronger
baseline can detect an erroneous edit after it happens; conversion seeks to
avoid that edit rather than replace post-effect verification.

D, fixed before formal: exactly 32 complete cells; typed12 exact intended edits,
typed4 no-input refusals (stale/unknown), untyped8 wrong saved effects. All admitted
programs4 physical emissions, exactly one text change, correct direction/range
readback, no replay, focus endpoint matches, all32-byte keymaps empty, native
app/Xvfb exit0, complete hashed artifacts. Thirteen named semantic corruptions
must be rejected, including fully rejoined wrong saved effects. Any violated
scientific gate is FAIL; first infrastructure/partial cell is STOP and stops
the allocation. One candidate, one auditor, zero retries. Formal output <=2MiB;
candidate90s+3s kill grace, host attach105s; auditor30s+3s, host45s. Per-IPC frame3s,
fresh Xvfb startup3s, own-child cleanup1-3s. These configured waits are not a
hard real-time or daemon-stall proof. Native input may already have occurred
when a deadline or collector fails; preserve partial evidence and do not replay.

C: No new mechanism may be needed beyond conventional UTF16 conversion and
saved-text verification. Baseline confusion is deliberately constructed in a
proposed numeric adapter, not a claimed existing Agent Interface defect.
Two widgets are not independent applications; fixed-order cells confound timing.
S06 is staged different content before admission, not a concurrent writer race.

U: No model/human/task benefit, latency distribution, tokens, accessibility,
real application integration, durable filesystem fsync, other toolkit/OS,
composition/IME, normalization equivalence, segmentation/version policy,
grapheme-atomic edits or partial-cluster semantics. ZWJ/flag/accent occur in
prefixes; their ASCII suffix ranges avoid partial clusters. A declared index
unit is necessary for this adapter but not sufficient for full edit semantics,
focus/authority/freshness after admission or #49 promotion. No host GUI, user
clipboard, GPU or prior consumed allocation is used. N/common deadline remain
unconfirmed, not reset; no new worker is launched.

Analytical reduction: for a scalar boundary n, its UTF16 boundary is the sum
of one unit for each BMP scalar and two for each supplementary scalar before n.
This preserves endpoint order, including backward selection. The independent
oracle uses UTF16 byte slicing rather than importing that conversion. The
remaining measured property is actual Qt selection/native replacement/receipt.
Qt's [QTextCursor documentation](https://doc.qt.io/qt-6/qtextcursor.html) describes
16-bit QChar positions. That current Qt6 source is motivation, not evidence for
the installed Qt5; this allocation records its Qt5 document counts and range
readbacks. No general Unicode segmentation implementation is supplied.

Fixed image is a child of prior clipboard image18835dcb..., adding python3-xlib
only. The missing-Xlib dependency attempt, policy import-red, original post-
construction auditor KeyError and its corrected raw-only check are retained.
Construction P01 four actual cells passed. Construction02 stopped at its first
P02 cell: an untyped range started inside a supplementary surrogate pair and
fixture selection reply raised UnicodeEncodeError/EOF before replacement. Its
raw/app stderr/source/container exit1 and absent native app exit record remain
unchanged. Construction03 uses P05 instead, avoiding that undeclared partial-
surrogate behavior, plus P03/P04, to check conversion/refusal branches. The
runner now records already-exited child return codes on future errors. All
construction outcomes are excluded from32 formal counts; formal source cases
were predetermined before this construction STOP and remain unchanged.
Three runtime implementation files are exact Git bytes from fb556b3d...;
empty research namespace initializers avoid importing unrelated session code.
No shared runtime/workflow/import/discovery/default or common index changes.
