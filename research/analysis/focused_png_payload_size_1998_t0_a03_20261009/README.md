# Focused PNG payload size — Issue #1998 A03

This package tests whether exact PNG crops can reduce canonical serialized payload bytes after base64 and identity/geometry metadata, with FULL_FRAME fallback whenever a crop does not save bytes. Three deterministic RGB8 patterns and 23 fixed valid/invalid request cases are used.

The result is limited to the declared synthetic PNG serializer. It does not measure Pillow timing, live observation encoding, model tokens, transport cost, visual target quality, GUI correctness, or task success. See `PROTOCOL.md` for the frozen gates and scope.
