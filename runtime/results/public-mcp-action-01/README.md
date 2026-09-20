# Primary public MCP action use (draft)

One owned WSL Xvfb/Tk allocation and one stdio MCP server were used. The primary agent saw the initial image, then supplied one explicit program to focus/click, type mcp-save-3546, save, wait 50 ms, capture and release. The SDK client forwards that decision; it contains no model or action-selection policy. The source sequence/binding and bounded lease were caller supplied, not server-issued authority.

The action completed with recovery_required=false; independent effect.json records the saved text. The returned image remained empty/unsaved. No input was replayed and no additional observation was requested. Thus task effect is supported by application readback, not by the returned image. The initial and action images were both viewed by the primary agent.

This is SDK-mediated primary use, not a host-registered direct MCP tool call. The clock interval in RESULT.json includes the call and serialization, not model deliberation or image presentation; it does not measure useful feedback or semantic completion. No token or speed comparison was made.

The existing fixture synchronously logs key/button events to a Windows-mounted /mnt/c directory and writes its saved effect there. That is an uncontrolled possible event-loop delay, not a proven cause. Do not generalize the stale capture to ordinary applications. The fixture and backend were not modified.

The SDK client and owner exited 0; both tracked GUI children were reaped. Descendant verification remains false. The source revision and file hashes were inspected after the run (no implementation edits occurred during the allocation); this is not full launch attestation. Raw paths in receipts refer to the original results-local/public-mcp-action-01 directory. The archive preserves the original directory structure and every file hash is listed in RESULT.json.

Draft integration evidence only; formal container and independent-review gates remain outstanding. No sensor work or secondary model was used.
