# #1349 XTerm transfer freeze

H/T/D/C/U and all thresholds are frozen in Issue #1349.

Only transfer factor: the #1188 purpose-built Tk sentinel is replaced by a real XTerm rendering surface whose standard-library child owns authoritative VALID/HARD state and progress. Planner gap40ms, action cadence5ms, hard offsets22.5/27.5/32.5ms, WAIT baseline, cached guard logic and independent effect accounting remain fixed.

Controller admission uses only a fixed XTerm pixel ROI (0,0,180,20) captured with XGetImage. VALID/HARD exact digests are calibrated before each measured case. Text/progress and fixture authoritative logs are not used for admission. AF_UNIX APPLY_PROGRESS is accepted by the fixture only while authoritative state is VALID; authoritative logs are read only after acting.

Excluded construction is3 matched pairs with disjoint seed, one per hard-offset class after shuffle. It may repair plumbing only; it cannot change thresholds or the formal24-pair schedule.

No XTEST/keyboard/mouse action exists in this study. Private Xvfb/XTerm still requires a fresh #60 live lease before construction/formal.
