# C06 pre-execution source amendment

The initial frozen audit source had no executable mutation harness despite the preregistered 4/4 corruption-control gate. No candidate or auditor execution had occurred and no raw output existed when this was found. Before execution, the auditor source was amended to run four in-memory adversarial mutations (missing row, duplicate row, changed exact probability numerator, and injected oracle/future-information field) and reject all four. Candidate and H/T/D/C/U are unchanged. This amendment supersedes the initial audit.js blob for the upcoming single C06 execution; both commits remain in branch history.

