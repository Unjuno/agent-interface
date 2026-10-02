# Raw transcription correction — construction-01

The earlier construction package commit retained a manually transcribed CONSTRUCTION_RAW.json with duplicate effectfulHostCalls/callsAfterRetry members in the numeric row. Standard JSON parsing is last-member-wins, so the first raw-only audit accepted that ambiguous transcription.

The single construction invocation's captured stdout shows the numeric row once, with effectfulHostCalls=1 and callsAfterRetry=1. This additive correction retains those exact captured bytes below a new path and pins the complete byte hash before JSON parsing. The original files remain unchanged for provenance but are superseded and not authoritative. No experiment or candidate was rerun.

Corrected raw SHA-256: 7248f86c5678ed0ea1db17b7df416c01da6585a0bdcb06bc3f7cdd7f29693c06. Corrected raw-only audit: PASS_JSON_PRIMITIVE_TERMINALITY_CONSTRUCTION, five rows.