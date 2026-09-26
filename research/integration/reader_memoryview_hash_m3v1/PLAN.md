# #4451 reader memoryview hash allocation plan

H/T/D/C/U is fixed by Issue #4451. This file fixes the executable denominator: formal uses one 1,048,576-byte corpus of 4096 exact 256-byte records, cursors 0/2048/4064/4096, max_records32, BASELINE vs MEMORYVIEW, three fresh-process repetitions (24 resource workers), then two untimed contract workers. Construction uses 64 records and cursors0/32/64 with one repetition and is excluded.

Formal decision: source/input/process/receipt parity; at cursors2048 and4064 candidate traced peak lower in all matched reps and median peak ratio <=0.75; median wall and CPU ratios <=1.20; contract parity/fail-closed controls; independent audit errors=[]; ten effective evidence mutations rejected. Cursor0/end are descriptive. Formal one invocation, reruns/replacements/exclusions/tuning0.

No shared-reader modification is included in this research branch.
