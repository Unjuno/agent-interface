# Development calibration

Official LibreOffice SDK documents Writer text documents as `XReplaceable`; `replaceAll(SearchDescriptor)` searches/replaces descriptor-defined matches in one method call and SearchDescriptor exposes `SearchRegularExpression`.

Private Writer probe established:
- exact regex `^book$` on text `book`: replace count 1, final `bookkeeperoffice`;
- same call on `boox`: count 0, final `boox`;
- two-RPC baseline read `book`, competing append completed to `bookx`, then unconditional set -> final `bookkeeperoffice` (completed append lost);
- exact replace after completed append -> count 0, final `bookx`;
- candidate with append-first delay -> `bookx`; replace-first -> `bookkeeperofficex`;
- 20 zero-delay development races -> all `bookkeeperofficex`, no hybrid/lost append.

Development rows are excluded from the formal decision.

Additional development finding: a 10 ms client-side delay did not guarantee UNO server execution order; one delayed-candidate trial linearized replace before a still-running append. Formal design therefore never derives server order from client delay/timestamps. Deterministic completed-before-call conditions establish both serial orders; concurrent arms accept either serializable result and only reject hybrid/lost-update outcomes.
