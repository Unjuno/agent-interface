# Golden v3 CLI adapter successor (#2172/#2186)

Adds an authority-neutral adapter after the machine-readable v3 schema freeze. It maps dispatch outcomes while keeping task success distinct from program completion, partial effects representable, cleanup errors non-success, and authority_granted=false. This is a stdlib contract test; no GUI/model/input/network execution.

Decision: PASS_GOLDEN_V3_CLI_ADAPTER_CONTRACT_SCOPED after the independent tests pass. Live adapter integration and fresh golden smoke remain separate gates.
