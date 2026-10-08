# Acceptance-scoped immutable GTK verifier (#2895)

This verifier checks the #2884 raw summary against the formal boundary without rerunning or rewriting it. It intentionally requires embedded raw event traces; an events_path string is not accepted as a raw event trace. The expected current result is STOP_MISSING_RAW_RECEIPT_BUNDLE until the individual raw event/effect files are retained.
