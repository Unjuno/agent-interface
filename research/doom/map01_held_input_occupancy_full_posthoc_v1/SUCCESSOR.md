# Frozen successor question from the retained #428 failure

Do not modify or rerun #428.

The next task may change exactly one mechanism: interval reconstruction for hold steps interrupted before `keys_held`.

Required cases before complete-log computation:

1. zero admissions then terminal/release -> exact zero task-key occupancy;
2. partial admission(s) then independently verified empty release -> any-key lower bound 0, upper bound earliest admission attempt to earliest verified empty release;
3. all requested admissions but no `keys_held` marker before interruption -> conservative any-key interval without claiming full-keyset establishment;
4. normal completed holds -> unchanged existing semantics;
5. cancellation after `keys_held` -> unchanged existing cancellation semantics.

The exact retained v39 `cover-4:10` sequence must be a frozen regression control. Only after these semantics pass independent synthetic/corruption tests should a NEW complete v38/v39 retained-log computation be allocated.
