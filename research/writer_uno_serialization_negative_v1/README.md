# Writer UNO serialization negative v1

A narrow real-Writer concurrency experiment. It tests whether compare-then-set, final recheck-then-set, or `lockControllers()` can serialize an external UNO text mutation. The expected useful result is a bounded negative result, not a production implementation.
