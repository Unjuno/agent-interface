# #8406 T1 A13 — schema-constrained consolidation output

A13 uses A12's symbolic mapping prompt and dataset but passes a JSON Schema to Ollama's `format` field for consolidation calls. The schema enumerates valid claim kinds. Query calls remain in JSON mode. This isolates whether constrained output prevents A12's repeated out-of-enum `rare_exception` claim kind. The transition auditor still decides semantic faithfulness and conflict completeness. See `PROTOCOL.md` and `FREEZE.json`.
