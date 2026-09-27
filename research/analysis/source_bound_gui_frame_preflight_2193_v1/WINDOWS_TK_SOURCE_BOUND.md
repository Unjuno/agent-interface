# Windows Tk source-bound capture

Started a controlled 320x240 Tk window titled `Codex source-bound fixture`, rendered a white square, and wrote `windows_tk_fixture_receipt.json` with `target_present=true` before capture. The exact Python process/window identity was observed twice through computer-use; a fresh screenshot was returned for the exact window. No keyboard or pointer action was used. Accessibility text was null.

Conclusion: controlled real-window capture is viable on this Windows host. This establishes source-bound acquisition only, not pixel decoding, receipt alignment, model accuracy, or gameplay transfer. Next capture both target-present and target-absent states with a receipt-bound frame hash or native pixel reader.
