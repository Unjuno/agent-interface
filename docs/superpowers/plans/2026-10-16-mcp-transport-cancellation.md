# Public MCP transport cancellation boundary

**Goal:** Distinguish accepted cancellation, pending worker custody, possible
in-flight presses and verified release through the actual public guarded tools.

**Architecture:** Select process/query/observation workers on the real MCP owner,
bridge and session with existing Fake X owner/read clients. Gate press-send,
press-sync, release-send or release-sync; retain pending/cancel/busy/lookup and
fake bitmap versus backend ledger separately. Never add another input writer.

**Constraints:** No native display/input, provider, WSL/container or allocation.
Fake transport barriers and host event order are not physical latency bounds.

- [x] Execute four blocked boundaries plus stable control. While the original
  worker is live, require pending lookup, no release confirmation, unchanged
  original deadline, and busy refusal for new input/close/recovery.
- [x] Resume the exact in-flight call; verify suffix refusal, same-call result
  retrieval, verified fake cleanup and old-authority refusal. Preserve the late
  press possibility after cancel acknowledgement and the empty-bitmap versus
  unverified-release distinction.
- [ ] Run affected normal/-O suites, retain source/raw/conditions and a saved-only
  audit, then review/integrate without claiming finite native release.
