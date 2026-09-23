# Construction history

- construction-01: `STOP_SETUP_XAUTHORITY`. Unit tests 3/3 passed, but before the first scientific operation Python-Xlib tried inherited `/opt/xvfb/.Xauthority`, which did not exist. No task click/effect row was produced. This is setup-only evidence.
- Repair before freeze: create an allocation-owned empty Xauthority file and export its exact path to fixture/controller while Xvfb is started with `-ac`. No schedule, cache policy, semantic resolver, guard, target/effect, threshold or decision gate changed.
- construction-02: `STOP_SETUP_XAUTHORITY_PARENT_ENV`. The child environment was corrected, but the parent Python-Xlib authentication resolver still read inherited `os.environ`; again no semantic click/effect row was produced. Repair: bind the same allocation-owned Xauthority path in the parent before `Display()` creation.
- construction-03: excluded eligible construction. 16/16 operation rows reconciled, candidate warm hits 3/3, required deopts 3/3 categories, wrong effects 0, raw audit errors=[], corruption controls 8/8 rejected. These rows are not pooled into formal.
