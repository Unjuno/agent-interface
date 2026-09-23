# Two-state Windows Tk source-bound capture

The same controlled 320x240 Tk fixture was launched twice, once with `target_present=true` and once with `false`. Each wrote its receipt before observation. The exact Python process/window identity was discovered and a fresh computer-use screenshot was obtained for each state, with no keyboard or pointer action.

Two receipts matched their requested launch states; the observations had distinct fresh screenshot IDs and window IDs. Accessibility text was null. Both processes were terminated afterward.

Conclusion: controlled two-state source-bound acquisition works. This does not yet prove pixel/receipt alignment or model accuracy; next add a native client-rectangle pixel hash and evaluate a tiny model.
