# Development

- Pure candidate logic: 5/5 tests before GUI calibration.
- First real Writer calibration bound the correct document/XID but both weak and bound fresh recovery produced `keeperofficebook`: UNO Frame activation/focus did not preserve an end-of-document caret. Document identity alone is insufficient for suffix recovery.
- Frozen-candidate development therefore explicitly reacquires the Writer insertion point with Ctrl+End only after document/XID binding and final guard, before suffix injection. This is Writer-specific transport policy, not a common text semantic.
- close/reopen same URL changed RuntimeUID 1 -> 3; bound policy rejected `STALE_DOCUMENT_ID` with zero input while weak policy accepted the old observation.
- Development fault matrix: wrong-document weak -> A=`bookeeperoffice`, bound -> `WRONG_DOCUMENT` zero input; focus drift weak -> B=`bookkkeeperoffice`, bound -> `FOCUS_MISMATCH` zero input; stale age weak accepted, bound -> `STALE_OBSERVATION`; changed A text weak -> `booxkeeperoffice`, bound -> `STALE_TEXT`. All releases empty.
- Final candidate also rechecks observation age immediately before first recovery input, after exact document re-read and XID/focus guard, to avoid aging across binding.
