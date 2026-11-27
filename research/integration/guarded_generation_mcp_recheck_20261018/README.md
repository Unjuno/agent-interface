# Current-main target-generation evidence through guarded MCP

Source revision: `4efa408b95a668458708acd25cf3c817e718cc58`. The exact source
files and hashes are in `SOURCE_FILES.json`; the normal and optimized test
outputs are retained as `normal.txt` and `optimized.txt`.

## Result

The current guarded MCP caller composes explicit startup policy, observation,
target alias minting, pre-input validation and result retrieval with both
process-generation evidence and opt-in window-lifecycle tokens. All 31 selected
tests passed in Python 3.13 normal mode (7.367 seconds) and `-O` mode (7.770
seconds). The selection included:

- stable process generation and same-XID process change refusal through MCP;
- generation change after the first modifier causes prefix cleanup, review
  requirement and refusal to reuse the old alias;
- same-process XID destruction/reuse and stale window tokens refuse the old
  alias, while the process-only control demonstrates its documented residual;
- lifecycle cancellation/expiry while the lifecycle reader or qualified
  observation persistence is blocked; the held Fake X prefix is released, the
  old source does not regain authority, and the reader retires;
- explicit MCP startup selection and qualified observation delivery preserve
  the pinned generation token.

## Scope and remaining boundary

This is current-source Fake X construction evidence through the standard
guarded MCP tool interface. It does not validate XRes/PID-namespace trust on a
live host, native lifecycle notifications, real target reuse, semantic
application effects, MAP01 success or recovery quality. Generation is sampled,
not atomically coupled to XTEST; a change after the final check can race the
input request. The Xlib input send/sync/readback path also remains synchronous,
so blocked platform I/O can delay physical release. These results qualify the
target evidence path, not bounded physical release or the full computer-control
objective.

Output SHA-256: normal
`952d0ffd81d7a6ef1a0cf93c27a71fa37ab9a8a81f16bf3f8894b3f310e5eaba`, optimized
`96502227cf25c82fd68e0510254257424215e12d2620ae8dca88ceceed4322a7`; source
list `7ef9edf5b6d48b7cc0f3a2dd7d26a0e1a67dcbd8302e15da166b131bf40a7d7b`.
