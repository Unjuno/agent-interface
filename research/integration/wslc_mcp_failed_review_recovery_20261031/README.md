# MCP failed review and recovery

Base `c8515d2880a7541d1abb45342a43cc774364ec9e`. A fresh WSLc allocation repeats the isolated Calc cancellation and later saved effect in PR #9876, then tries to review a distinct, unmapped, nonfocused X11 window. Review returns `needs_review`, changes scope and revision, and dispatches no input. Subsequent old-alias input and old-source mint are both refused. The previous saved effect remains present.

The same session then reviews the actual focused Calc window; old-alias input is refused as MISSING, and a distinct alias from the new source enters and saves A3=975. File snapshots show the original blank file, A1=731 and A2=864 after the delayed save, then A3=975 after continuation. Input-release receipts and final key/button state are checked. The successful review and continuation are a positive control for the failed review; the earlier PR #9876 independently exercised the successful path without the decoy.

`a11.zip` preserves the trial script, conditions, screenshots, top-level receipts and file snapshots. Nested receipt journals remain local and are represented by SHA-256 and size. Run `python audit.py` to inspect recorded state and independently parse the FODS snapshots. This is one failure mode in one controlled target, not a claim about all review failures, model-driven recovery or MAP01.
