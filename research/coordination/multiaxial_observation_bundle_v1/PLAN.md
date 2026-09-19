# Multiaxial observation source-capability gate v1

Task: `MULTIAXIAL-SOURCE-CAPABILITY-GATE-20260917-001`
Publication base: `6a36ecbdf782d02d280b31f368d5542b9527f591`
Issue: #760; parent #753.

Single factor: observation compilation policy (`RELEVANCE_ONLY` vs `CAPABILITY_GATED`). Source registry, relevance scores, requests, source-capability/context mask, item budgets and presentation schema are frozen inputs. No model calls.

Formal block: 6 cases x 4 repetitions x 2 policies = 48 deterministic rows, one runner invocation. Five malformed presentation controls. No same-ID rerun, replacement, or post-result source/query/gate changes.
