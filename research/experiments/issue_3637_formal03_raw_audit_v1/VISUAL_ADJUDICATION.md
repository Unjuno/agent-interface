# Manual visual check of hash-verified formal-03 counter pixels

I rendered `evidence/counter_contact_sheet.png` from the exact Git-blob frames listed in `evidence/predecessor_gitblob_manifest.json`, after `audit_result_gitblob.json` verified the tree and each referenced frame. The contact sheet has 16 panels: for each of four arms, positive before/after then no-effect before/after.

On visual inspection, all four positive pairs show `COUNT 0` before and `COUNT 1` after (with the refreshed `VERSION 2`); all four no-effect pairs show `COUNT 0` both before and after. The button changes hover appearance after pointer movement, which can change the full-frame hash without changing the counter label.

The reproducible pixel check is deliberately narrower than OCR: for the fixed ROI `(108, 18, 205, 46)`, all zero/no-effect crops share SHA-256 `2fa4a9dda7e70abfcce3b153264b8fc4a296708fbcea9f66a7823924a953de46`; all four positive-after crops share `47f5cf580e9dfac9119ced9164d0b9b6cfeeeac68b1f8cd559a7ae9bf12e1411`. Human visual inspection supplies the transcription; the script independently proves crop identity/change, frame hash closure, and raw path inventory. No OCR or new GUI observation is claimed.
