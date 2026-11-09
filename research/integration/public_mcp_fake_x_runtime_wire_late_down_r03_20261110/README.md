# Public MCP Fake X late-down baseline reproduction R03

This packet reproduces the pre-R04 standard-caller Fake X test before changing
the late-down state model. The test source is commit
`2f8f10ae9d` (`Document delayed input evidence boundary`). It uses the public
guarded MCP caller and captures the emitted 36-byte XTEST press request, but
the post-readback late-down state is hard-coded into the fixture model rather
than derived from those bytes.

The single targeted case passed once under normal Python 3.13 and once under
`-O`. These runs are a local reproduction of the existing modeled result, not
live X-server behavior. R04 follows with the same caller case and derives its
modeled transition from the captured request. Raw stdout and receipts are
retained and covered by `SHA256SUMS.json`.
