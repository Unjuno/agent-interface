# Single-acquisition image presentation (research only)

Issue #4404. See PLAN.md and CANDIDATE.diff. The existing runtime is unchanged.
This experiment requires quiescent immutable artifacts; the candidate is not a
drop-in mutable-file replacement and removes a second-acquisition change check.

The baseline executes complete upstream review_bytes with compact=False. The
candidate hands the selector's already-hashed bytes to the same presenter.
Source identity is recorded in VENDOR.json and FREEZE.json.

Formal source/readback must precede the six worker conditions. Each execute.py
formal INDEX is once-only; do not rerun an existing formal directory. The controls
command has its own fresh directory. Audit.py reads saved data only.

After measurement RESULT.md records all outcomes, including any STOP/HOLD.
Model/GUI/input, whole-runtime acceptance, memory benefit and real-host latency
are not inferred from this scoped result.
