# Contract argument: inherit cancellation, not ancestor waiting

## Variable table
| Symbol | 日本語の意味 | SI unit | Definition | Domain / assumption | Type |
|---|---|---|---|---|---|
| d | 現在の葉の深度 | 1 | root depth0, leaf depth d | finite integer; implementation0..7, live d=2 | integer scalar |
| i | フレームの添字 | 1 | index on the registered path | integer0..d | integer scalar |
| A_i | 当該フレーム固有の活動状態 | 1 | current task_active | Boolean; not already ancestry-aggregated | Boolean scalar |
| R_i | 当該フレーム自身の割込み解消 | 1 | current interrupt_resolved | Boolean | Boolean scalar |
| L_d | 葉自身の完全な復帰条件 | 1 | same scope/source/target/queue, active, resolved, known result | Boolean; inherited strict contract | Boolean scalar |
| B | 祖先証拠の完全性と現在束縛 | 1 | all registered ancestor records present, scoped and source-current | Boolean; trustworthy coherent snapshot assumption | Boolean scalar |
| E_d | この契約の復帰適格性 | 1 | L_d AND B AND every ancestor A_i | Boolean; evidence only, not OS authority | Boolean scalar |

All quantities are dimensionless. No time, bytes, probabilities or physical units
are mixed in the logic. ns timestamps in the live log are independent diagnostics.

## Assumptions
The saved chain names distinct complete root-to-leaf frames in one task lineage.
Its current records are truthful and coherent at the decision point, with no
mutation before the directed effect. A local active flag describes only its frame.
Canceling any ancestor forbids descendant task work. Ancestor waiting means it is
waiting for its descendant; it is NOT a prohibition on that descendant executing.
Only liveness is inherited here; other ancestor conditions govern its own future
continuation. This is an explicit task contract, not a claim about every GUI.

## Necessity and sufficiency under these assumptions
Define
    E_d = L_d AND B AND (AND over i=0..d-1 of A_i).
For d=0 the empty conjunction is true and there is no ancestor evidence to acquire.

Necessity: if L_d is false, the leaf's own required condition fails, so leaf input
is ineligible. If B is false, at least one required current ancestor fact cannot
be established; the evidence-based contract must yield. If any ancestor A_i is
false, the explicit inherited-cancellation rule forbids leaf work. Therefore each
conjunct is necessary for an eligible leaf continuation.

Sufficiency: suppose every conjunct is true. L_d establishes every declared local
condition. B supplies the complete matching current ancestry. Every ancestor is
active, so no inherited cancellation prohibition applies. By the stated contract
these are all required conditions. Therefore the continuation is eligible. This
is not a proof of arbitrary application safety or a grant of native input authority.

This also follows by induction down a finite chain: the root's inherited liveness
is A_0; appending child i replaces inherited liveness with the previous conjunction
AND A_i. Thus a canceled prefix can never become live merely because a child has
its own true flag. The implementation checks the same ancestor conjunction after
the exact strict leaf gate, limited to at most8 registered frames.

## Counterexample to local-only validation
Take d=2, A_0=false, A_1=A_2=true, B=true, L_2=true. A checker using L_2 alone
allows. E_2 is false because its ancestor conjunction includes A_0. This requires
no malformed or fabricated record: truthful per-frame facts already suffice.

## Counterexample to applying every ancestor gate
Take d=2, all A_i=true, B=true, L_2=true, R_0=R_1=false, R_2=true. This is the
ordinary state where the ancestors await the child and the child's terminal modal
has closed. E_2 is true. A checker additionally requiring R_0 AND R_1 rejects.
If child completion is the only transition that resolves the ancestors, repeated
unchanged-state evaluation cannot make progress. The live experiment tests the
single-decision over-refusal, not an unbounded wall-clock deadlock.

## Empirical residual and limits
The argument establishes the declared predicate relation. Only execution can check
that the real Tk nested windows expose these states, that XTEST input reaches the
leaf, that cancellation remains visible, and that input/effects/cleanup are retained.
The pilot supplies those narrow observations. It does not establish how a real
application derives or authenticates the active flags, nor atomic check/use.

## ERROR CHECK
Both counterexamples use well-formed truthful records. Missing evidence is not
classified as actual cancellation. Local flag meaning and the non-inherited wait
condition are assumptions; changing them changes the contract. OS-input authority,
whole-task completion and natural reliability are outside the proof.
