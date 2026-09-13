# Same-task assistant replay: examples remove one observed retry, time unchanged

Actual assistant runs journal-calc-01 (interactive_v17) and journal-calc-02
(interactive_v18) use Calc, seed 991022, A1=532, A2=590, Excel save confirmation,
the same session_v16 backend and persistent receipts. Source manifests, identical
goal dictionaries and identical accepted step arrays are checked mechanically.
Run 02 received basic examples in ready and used the correct chord shape first.
Both independently scored saved workbooks pass; 39 exact frames and every declared
delivery reference are audited by compare_calc_examples.py.

| Endpoint/count | Before examples | After examples |
|---|---:|---:|
| Submit commands | 3 | 2 |
| Accepted programs | 2 | 2 |
| Rejections | 1 | 0 |
| Clock commands | 3 | 2 |
| First capture → independent score | 97.873 s | 97.515 s |
| First acceptance → score | 41.946 s | 71.565 s |
| Modal terminal → confirm command | 26.434 s | 39.442 s |
| Final terminal → score | 13.882 s | 30.650 s |
| Local accepted programs | 0.947 / 0.661 s | 0.875 / 0.580 s |
| Delivered JSON | 29,195 bytes | 27,670 bytes |

Before examples, rejection→retry acceptance alone took 29.963 s. After examples,
that retry disappeared but other external gaps increased. Selecting the first
acceptance as the only start would hide the earlier retry cost and distort the
comparison. There is no demonstrated end-to-end speedup from this pair.

This is sequential self-use by the same assistant, not randomized or independent
model trials. The assistant already knew the corrected syntax in run 02, and tool
polling, output budgets and response timing varied. Model inference/transport
endpoints and exact model settings are not captured. No causal attribution to
examples, statistical significance, token savings or human-level cadence follows.
The useful evidence is that live examples are present and usable, correctness is
preserved, and external control gaps still dominate tiny local execution changes.

Future work should target required planner boundaries and verification delivery.
A bounded prepared next-step proposal may help predictable modal workflows, but
must remain no-authority until a fresh predicate and ordinary admission pass.
Unexpected modal states must invalidate proposals. Preserve a normal baseline and
negative states before attributing a timing improvement to such a mechanism.
