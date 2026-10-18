# F02 EOF notification candidate construction — #59

New additive branch/path; E02/F01 first outcomes and PR7295 unchanged.
H: exact E02 candidate with one EOF raise after its reader loop delivers
queued ready/terminal first, then typedfailure causedbyEOFError rather than
silenttimeout; malformedJSON retainsJSONDecodeError cause.
T: actual4fresh subprocess stdoutpipes, no GUI/game/model/nativeinput.
D: unittest realchildlive/readerretired/eventorder/cause/ownedreaping assertions.
C: E02 candidateSHA pinned; AST transform only adds postloopraise to originaltry.
U: historical reader/waitAST, not fullcontroller, not productiondefault/recovery.
Failure notification is consumed once; persistent failed-state and repeatedwait,
event-shape validation, normalprocess exit races remain unqualified. A terminal
event completing its predicate is delivered beforeEOF, not turned into failure.

Construction RED: legacyE02-backedcandidate4tests,3EOFassertionsFAIL/JSONcontrolPASS.
Then postloopEOFraise candidateGREEN4tests. These are construction allocations,
not new formally frozen game/controller results. No prior allocation replay.
ActualOSpipeclosures and children are testowned; cleanupterminate/killfallback
reaps child, joinsreader andassertsretirement. No3ssurvival/latencyclaim.
Independent review and separately frozen formal successor remain required.
