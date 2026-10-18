# CI fixture closure and native regression follow-up

The prior 70-method author result is unchanged. At head eb3f83b026, GitHub's
native-mcp job failed two ProgramLocalTargetTests because their manually
constructed X11Backend objects lacked held_keycodes. The same two errors were
reproduced locally among 12 focus/activation methods; the full first log is
retained here. Only those two fixtures now initialize an empty ledger.

Focused suite including focus/activation: **82 methods PASS**. Production
backend source is byte-identical to eb3f83b026. A distinct reviewer scanned
all X11/guarded __new__ fixtures reaching real preflight and found only these
two missing initializations. This is a static closure check, not a merge vote.

Two new ordinary native regression methods are added to the existing Xvfb
suite. One holds Shift across paced text("Ab") and requires the independent
Tk save artifact to contain "AB"; the other requires held-letter collision
refusal before any native program input. Their native execution is pending
at this source commit; it must be linked to the exact tested revision before
claiming PASS. This does not replay or change #8339's consumed six-cell result.
The existing fixture already clicks its Entry, so it does not reuse the
incorrect direct-Entry native focus protocol from that historical experiment.

Earlier CI evidence (before these fixture/test edits):
- Failed native-mcp: https://github.com/Unjuno/agent-interface/actions/runs/37649438974
- Passed X11: https://github.com/Unjuno/agent-interface/actions/runs/37649438856

The earlier X11 job checked synthetic merge f29c51374f868996eeb476f3e7f8b56be0d347b4
(eb3f83b026 merged into dae92e1), not an arbitrary later main. Its two suite
counts were 116 and 70; the latter mixes native and inert methods. It predates
the new native regression methods and cannot validate them.

Fresh content review covers the complete original #8308 + repair, against
798ac5ad709168ff1d27b115f10f4f96b126bb71. Root authored the repair and does not
vote. The own PR will target main directly to integrate prerequisites and fix
together, leaving the prerequisite author's branch untouched. Content quorum,
current-main combined-tree check and effective rules remain separate gates.
