# Proof

Let targets be `x_0,...,x_n`. A serialized physical pointer ends transition `i-1` at physical endpoint `x_{i-1}`. Under the stated alias rule, activating any logical cursor for the next target `x_i` must still materialize the same physical transition from `x_{i-1}` to `x_i`, whose cost is `m_i=|x_i-x_{i-1}|`. Remembered logical positions do not alter the physical predecessor endpoint. By summing each required transition, every alias labeling has total physical reposition cost `sum_i m_i`, identical to SINGLE.

If a separately declared switch/warp primitive may replace transition `i` with cost `s`, the optimal transition cost is `min(m_i,s)`. Therefore total gain is

`sum_i m_i - sum_i min(m_i,s) = sum_i max(m_i-s,0)`.

Strict gain occurs iff at least one transition has `m_i>s`. This gain is attributable to the new relocation primitive, not logical cursor multiplicity.
