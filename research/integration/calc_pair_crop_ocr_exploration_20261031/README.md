# Calc two-cell OCR exploration on retained screens

Five separate offline, no-GUI-input WSLc OCR runs, each with its own conditions and container, on previously captured isolated Calc images. Each exact container ID was confirmed absent. Conditions and TSVs, crop images, stderr and raw receipts are retained. Host mount paths in public conditions are placeholders.

The first crop gave `73` at confidence 0 and `864` at 13.93. A later exploratory adjustment removed blue selection pixels and used Lanczos scaling; on that same positive image it read `731` at 90.06 and `864` at 96.53. This is tuning on the positive image, not an independent replication. Fixed preprocessing on one separate blank image produced no tokens; on one wrong-value image it read `731` and `863`, avoiding false acceptance. The subsequently tested binary threshold method produced unknown for positive, blank and wrong. All thresholds remain 90.

This evidence does not qualify general OCR accuracy, target identity, actual saved effects or control reliability. The crop adjustment has not been independently validated across fonts, layouts, values, focus or display states. Source images are retained for audit. The separate A03 live graph continued to stop at OCR confidence 89.47 and remains a failure; do not use these offline outputs to rewrite it.
