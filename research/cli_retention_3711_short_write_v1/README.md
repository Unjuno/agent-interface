# Issue #3711 short-write protocol archive

This path preserves the exact preregistered construction protocol from closed
PR #3726. `PROTOCOL.md` is copied byte-for-byte (SHA-256
`59f5df7485922b35403d50aacf5d92e0774d56b6ea4a0e750a7e62142f296f3c`); its
historical status line remains unchanged. See `INTEGRATION_STATUS.md` for the
later implementation links and the actual cross-platform CI disposition.

The short-write handling and explicit flush changes are on `main` through PRs
#3727 and #3729. This archive makes no claim of real OS-pipe truncation,
consumer disconnect, GUI/model activity, or broad reliability.
