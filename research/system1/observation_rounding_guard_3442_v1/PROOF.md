# Conditional guarantee and information-loss boundary

## Variables (all mathematical units are SI dimensionless, 1)

| Symbol | Japanese meaning | Unit | Definition | Domain/assumptions | Type |
|---|---|---|---|---|---|
| x | 丸め前の観測値 |1| (p,v,a,s) | finite binary64 components in [-4,4] | real 4-vector |
| p,v,a,s | 正規化位置、速度、観測年齢、scope指標 |1| components of x | no physical-scale interpretation; age is not seconds | real scalars |
| V | 元観測値が制約内という述語 |1| abs(p)<=11/10, abs(v)<=7/20, a<=9/10, s>=1/2 | conjunction; exact rational constants | Boolean function |
| Q | binary32への変換 |1| componentwise nearest rounding, ties to even | correctly rounded finite input | vector function |
| q | 丸め後観測値 |1| Q(x) | supported finite binary32, magnitude<=4 | real 4-vector |
| q_i^-,q_i^+ | 前後の表現可能値 |1| immediate binary32 neighbors of component q_i | zero uses negative/positive minimum subnormal | real scalars |
| L_i,U_i | 元の値を囲む下限・上限 |1| (q_i^-+q_i)/2, (q_i+q_i^+)/2 | closed bounds, endpoints conservatively included | rational scalars |
| B(q) | 丸め前観測値の包含領域 |1| Cartesian product of [L_i,U_i] | same conversion for each component | set of real 4-vectors |
| A | 区間ガード |1| true iff B(q) is a subset of V's valid set | unsupported inputs return false | Boolean function |
| f | 丸め後だけを見る判定器 |1| any deterministic function of q | has no independent source information | Boolean function |

## 1. Enclosure

For one component, consider any real source y with Q(y)=q_i. If y<(q_i^-+q_i)/2, its distance to q_i^- is strictly smaller than its distance to q_i, so nearest rounding cannot yield q_i. Therefore y>=L_i. The symmetric argument gives y<=U_i. At an exact midpoint, tie-to-even may assign the source to either this value or its neighbor. Including both endpoints can only enlarge the admissible source set, never omit an actual source. Applying this reasoning to all four components gives x in B(q).

## 2. Guard implementation

V's valid set is the intersection of six axis-aligned half-spaces. Every point of B(q) is in that set exactly when L_p>=-11/10, U_p<=11/10, L_v>=-7/20, U_v<=7/20, U_a<=9/10 and L_s>=1/2. These are precisely certify.allowed's six comparisons. Bounds and comparisons use Python Fraction, so no additional rounding error is introduced after decoding each binary32 value. The independent auditor instead enumerates all16 corners and checks V; for an axis-aligned box and these half-spaces the two criteria are equivalent.

## 3. Conditional absence of false permission

Assume the source/conversion conditions above. If A(q) is true, every point of B(q) satisfies V by part2. The actual source x belongs to B(q) by part1. Hence V(x) is true. Therefore A(Q(x)) cannot be true for an invalid source. This is not a statement about physical sensor truth, fresh state, authentication, effect or execution permission. The code returns only a diagnostic validity Boolean.

## 4. Unavoidable ambiguity

Suppose x and y have different validity labels but Q(x)=Q(y)=q. A deterministic f reading only q must return the same value for both. If it returns true, it permits the invalid source; if it returns false, it refuses the valid source. Thus no such f can both permit every valid source and refuse every invalid source. Widening q to binary64 is still a function of q and cannot escape this argument. A tie-conservative enclosure may refuse additional boundary values, so no optimality claim follows.

## 5. Why this does not refute the predecessor

The predecessor defines its tensor operations on already binary32 values with tensor-compatible rounded constants. Our V instead defines a new pre-conversion observation contract with exact rational bounds. These are different predicates on different domains. Agreement of the old override with its own binary32 teacher and failure to preserve V can coexist without contradiction. Original model-quality FAILs and the earlier proof's binary32 assumptions remain intact.

## Unit/error check

All features, thresholds, neighbor differences and interval endpoints are dimensionless. Addition, division by2 and comparisons are dimensionally valid. The deterministic conversion enclosure is a bound, not a statistical standard uncertainty: a probability distribution, combined u_c or coverage factor k is not justified. Earlier sensor error, scale conversion, non-nearest rounding, flush-to-zero, or arbitrary subsequent arithmetic would require a different enclosure. Unsupported values are not silently assigned this proof.

## Primary implementation references

- Python struct documentation, format notes: `f` uses IEEE754 binary32 regardless of native platform format; explicit `>` avoids implicit native endianness: https://docs.python.org/3/library/struct.html
- PyTorch2.10 Numerical accuracy: finite precision and lack of cross-platform bitwise guarantees: https://docs.pytorch.org/docs/2.10/notes/numerical_accuracy.html

These documents motivate explicit assumptions; the retained actual bits and independent oracle, not documentation alone, validate the tested conversion paths.
