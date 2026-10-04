# Current-main nominal boundary integration rescue

Original PR #6923, `fix/kernel-nominal-records-01a0ff2d-20261003`, source
`b84aa6a1260128bd70e2cbe1598a9c80b55f75ee`. Preserve all 35 original evidence
files, including historical first failures, six omission mutants, public/private
path distinctions and author-only authority qualifications. No old allocation,
matrix, producer, or mutant is executed. Evidence-only predecessor PR #6881 was
already separately rescued; it did not adopt this production repair.

Fresh current-main TDD: the original seven regression methods yielded five FAIL,
one ERROR (untyped release attribute read), and one existing observation PASS.
Six nominal guards were then added without removing existing temporal/release
checks. Complete kernel discovery now passes 50 methods normally and under `-O`;
current core discovery passes 92 methods. The source projection's ten Python files
and discovery workflow must remain exact to the published candidate pins.

This new integration is not retroactive approval of old author votes/custody.
Trusted sequential nominal API scope only: `isinstance` accepts subclasses;
hostile overrides, mutated fields, concurrency and clock authenticity are outside
scope. Typed release admission is not proof of physical release or task effect.

```sh
python3 -m unittest discover -s runtime/results/kernel_nominal_rescue_6923 -p 'test_*.py' -v
```
