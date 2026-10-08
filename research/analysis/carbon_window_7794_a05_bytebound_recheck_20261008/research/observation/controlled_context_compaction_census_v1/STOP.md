# #1585 workflow stop — source-first ordering violated

Task `CONTROLLED-CONTEXT-COMPACTION-PRIMITIVE-CENSUS-20260918-001` has **no scientific disposition**.

H/T/D/C/U were preregistered in Issue #1585. During intended construction, `analyze.py` was invoked before any remote source freeze. That analyzer hardcodes `formal_invocations=1`, so the first local output was formal-tagged and already revealed the census decision. The planned source-first formal allocation is therefore invalidated.

The output is retained unchanged as `PREFREEZE_FORMAL_TAGGED_OUTPUT.json`; it must not be promoted, pooled, relabeled as construction, or rerun under the same task identity. No model/provider/GUI/input operation occurred.

The mechanical observation motivating an A2 successor is retained: generic `request(method, params)` transport exists and spontaneous context compaction is documented, but the inspected pinned repository did not expose a demonstrated target-bound compaction request with an observable boundary. This is not accepted as a formal result under #1585.

A2 may change only workflow discipline: separate construction from formal, freeze exact ledger/source remotely before the single formal invocation, keep the scientific ledger/gates/candidates unchanged, and preserve #1585 verbatim.
