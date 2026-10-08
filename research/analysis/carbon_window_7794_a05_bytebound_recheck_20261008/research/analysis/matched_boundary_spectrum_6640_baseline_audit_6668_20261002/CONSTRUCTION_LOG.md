# Construction log

- Initial test pass: 2/3 PASS, 1/3 FAIL. The failing assertion incorrectly
  expected pooled Ochiai for `cache` to be zero because the predecessor's
  *matched per-stratum* comparator had no overlap. Those are different
  estimands: pooled exposed/unexposed failure association can be nonzero even
  when no stratum supports a matched contrast. The raw fixture showed the
  pooled value as `0.45860142333700366` for seed 0. No source result or
  predecessor artifact was edited.
- Correction: the test now independently computes the standard Ochiai
  expression from its four confusion counts and separately keeps the
  predecessor reconstruction check. This preserves and distinguishes the
  pooled-vs-stratified boundary rather than forcing either value to zero.
- This was an audit-construction test only. The analytic audit output had not
  yet been emitted when the assertion failed.
