# Conditional soundness, completeness and byte crossover

## Variable table / implementation contract

|Symbol|Meaning / 日本語|SI unit|Definition and domain|Type|
|---|---|---|---|---|
|x|変換前の観測|1 (dimensionless)|four finite binary64 components in [-4,4]; ordered position,velocity,normalized age,scope|vector R^4|
|q|丸め後の観測|1|componentwise correctly rounded binary32(x), nearest/ties-even|vector R^4|
|i|成分の番号|1|1,2,3,4|integer scalar|
|l_i,u_i|丸め逆像の保守的下端・上端|1|midpoints between q_i and its adjacent binary32 values; ties included|rational scalars|
|B(q)|元値の包含箱|1^4|Cartesian product of [l_i,u_i]|set|
|A|有効領域|1^4|abs(x_1)<=11/10,abs(x_2)<=7/20,x_3<=9/10,x_4>=1/2|set|
|N|観測メッセージ数|1|positive integer;16 per formal corpus|integer scalar|
|R|精度問い合わせ数|1|integer from0 through N|integer scalar|
|f|問い合わせ比率|1|R/N, from0 through1|scalar|
|C64,Csel|両方向の通信量|byte (information unit; not SI)|sum of actual fixed-format protocol bytes, including final status|nonnegative integer scalars|

Implementation: >cQ, >cQ4f, >cQ4d use explicit big-endian standard widths with no native alignment. Fractions represent the exact decoded binary64/32 value, not an intended decimal approximation. The old cell implementation is vendored byte-identically. Sources near unsupported infinity/overflow are excluded; nonfinite fine replies return UNKNOWN. Signed-zero cells are conservatively enclosed symmetrically. There is no sensor/calibration or temporal uncertainty in this model.

## 1. Enclosure
For any finite scalar rounded to q_i under nearest rounding, a value strictly below the midpoint to the previous representable value is nearer that previous value, and cannot round to q_i. Similarly, a value strictly above the next midpoint cannot round to q_i. Therefore l_i<=x_i<=u_i. Including both tie endpoints only enlarges the true preimage; it never excludes the original. Applying this argument to each component gives x in B(q). This relies on correct conversion and an unchanged original, not on its truth in the physical world.

## 2. Definite decisions
If B(q) is a subset of A, x in B(q) implies x in A, so VALID is sound.
If B(q) intersect A is empty, x in B(q) implies x not in A, so INVALID is sound.
Otherwise neither conclusion follows from the coarse payload alone. The receiver emits UNKNOWN or requests original precision; it does not select an arbitrary point.

The allowed set is an axis-aligned product. Box containment holds exactly when every finite lower bound is met by the corresponding box lower endpoint and every upper bound by its upper endpoint. Disjointness holds exactly when at least one coordinate interval lies completely outside its allowed interval. If no coordinate is disjoint, select any member of each coordinate intersection; their vector lies in both sets, proving the converse. These tests therefore need no sampling of box interiors.

## 3. Refinement completeness under the trusted-store assumption
The producer is assumed to retain x unchanged at a unique, non-reused observation ID. Upon the matching request it returns those original binary64 bits, not a freshly observed value. Receiver ID matching and recomputed coarse-payload equality detect the stated protocol inconsistencies. They do not establish truth/authenticity against a lying same-ID producer.

An exact binary64 payload carries x itself. Rational comparisons against the exact rational region bounds decide x in A with no further numerical error. Every definite coarse response is sound by section2; every unresolved response with the valid original refinement is decided exactly. Thus SELECTIVE64 and ALWAYS64 are complete and equal on the supported cooperative protocol. Missing, invalid or inconsistent refinement stays UNKNOWN; completeness is explicitly conditional on obtaining the original. No new observation freshness or execution authority is established.

## 4. Byte accounting and crossover
Header/status/query size is1+8=9 bytes. Four coarse numbers contribute4*4=16 bytes; four fine numbers contribute4*8=32 bytes. Thus a coarse packet is25 bytes and a fine packet41 bytes. The common final status is9 bytes.

C64 = 50 N.
Csel = 34 (N-R) + 84 R = 34 N + 50 R.

Subtracting gives Csel-C64 = 50 R-16 N. Since N>0, Csel<C64 is equivalent to R/N<16/50=0.32. Equality at0.32 is break-even for THIS wire only. All added quantities have units byte; N,R,f are dimensionless, so both sides are byte counts. This is an exact discrete accounting identity, not a performance model.

For N=16, R=2 yields644 versus800 bytes (156 bytes saved). R=8 yields944 versus800 (144 bytes extra). R=16 yields1344 versus800 (544 bytes extra). The cases deliberately expose both outcomes. Query latency, headers outside this binary stream, source storage, process startup and downstream usefulness are not represented.

## ERROR CHECK
Containment is conservative at ties; disjointness is proved for axis-aligned product constraints. The claim includes a truthful immutable producer, not just an ID check. Original precision remains different from current evidence. Both directions and common final statuses are included. Boundary-dense regression is not hidden by pooled averages.

## Primary documentation
Python3.13 struct: https://docs.python.org/3.13/library/struct.html
Python3.13 fractions: https://docs.python.org/3.13/library/fractions.html
Repository predecessor: #4045 / PR#4047, certify.py blob3b03f12c34dd64250deebb9cde78ea48a50a7b5e.
