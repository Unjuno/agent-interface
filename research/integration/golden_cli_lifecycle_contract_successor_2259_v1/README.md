# Golden v3 → CLI lifecycle contract successor #2259

Status: PASS_DESKTOP_VERTICAL_SLICE_CONTRACT_AUDIT_SCOPED

This static successor freezes four current-main source identities and maps ten lifecycle states from the golden desktop v3 route to typed CLI/core outcomes. Every row is explicit, task success remains distinct from program completion, partial effects remain representable, cleanup failure is non-success, unknown states fail closed, and no row grants authority.

This is a contract prerequisite only. It does not implement the adapter or run GUI/model/network/input/Docker. A live adapter requires a fresh successor.

Reproduction: run python audit.py.
