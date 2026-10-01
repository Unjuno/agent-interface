# Construction notes

## Prior analytic calibration and overlap

The Issue already contains a four-world analytic XOR calibration in comment #5926254207. This package preserves that conclusion and extends it to the declared policy baselines and controls; it is not an independent discovery claim. The original calibrated XOR decision loss is 1.0 before checks, 1.0 after either singleton, and 0 after the pair. At 0.1 per check the joint net value is +0.8. At 0.6 per check the same one-bit pair has net value −0.2. The nine-case package adds redundancy, diminishing returns, deadline, freshness/epoch, source-dependence, mandatory-gate, and low-decision-value checks.

## Pre-freeze iteration history

- Initial test discovery from the workspace root failed because the test fixture is intentionally opened relative to the experiment working directory. This was a harness working-directory error; no candidate formal run occurred.
- First correctly rooted construction suite: 8/10 passed. It exposed (1) the auditor returning action and loss in reversed tuple order for a failed mandatory gate, and (2) a test still reading a queries output key after the candidate schema was simplified to policy trees and score claims.
- Corrected both before freezing. Rerun from research_tmp_5869 with python -B -m unittest discover -s . -p test_construction.py -v: 10/10 passed.
- Changed the XOR calibration to the existing issue comment's 0.1-cost baseline, and added sensitivity checks for world probability, decision-loss utility, and query cost. The final construction suite count is 11; the exact result is recorded separately after execution.

These are construction findings only. No frozen candidate or formal auditor subprocess had run when this note was written.
