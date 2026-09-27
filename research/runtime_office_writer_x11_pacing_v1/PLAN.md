# Office Writer X11 pacing transfer v1 — frozen finite plan

Question: does the Calc pacing result transfer to a second real Office application?

Fixed formal order: **0, 12, 1 ms/character**. Each arm uses a fresh private Xvfb/Openbox/LibreOffice Writer session and a fresh native ODT. A fixed leading sentinel absorbs Writer's first-word AutoCorrect and is excluded from the 16-string scored corpus. The scored corpus is identical to the Calc pacing experiment.

Every arm must: reject a stale observation with zero backend emissions; admit the fresh task; verify empty terminal input release; save the native ODT; and be scored only after executor completion by an independent ODT ZIP/XML reader. No formal arm reruns. No model/provider/network.

TRANSFER_PASS requires: 1 ms exact, 12 ms exact, 0 ms semantically worse or at least not superior, plus all stale/release gates. If 1 ms fails, reject cross-app promotion. If 0/1/12 all pass, conclude application dependence rather than a universal lower bound.
