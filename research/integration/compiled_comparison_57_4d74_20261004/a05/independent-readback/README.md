# Independent readback of archived A05 records

These scripts independently reconcile and describe retained A05 records from source revision `58bcbb4c45501880db8782158ddd3add3b765984`. They use `git show` against that revision and do not run the producer, model provider, GUI, or study runner. Run them from any working directory inside a checkout containing that commit:

```powershell
python research/integration/compiled_comparison_57_4d74_20261004/a05/independent-readback/target_linkage.py
python research/integration/compiled_comparison_57_4d74_20261004/a05/independent-readback/paired_contrast.py
python research/integration/compiled_comparison_57_4d74_20261004/a05/independent-readback/raw_arm_cost_reconcile.py
```

The committed JSON files are the output of those commands. Re-running each command should reproduce the corresponding file.

`raw_arm_cost_reconcile.py` sums task and schema-preflight usage directly from 48 task records, eight evaluation records, six preflight records, all 26 provider-result records, and `HOST.json`. The raw provider totals exactly equal task-plus-preflight totals. All-attempt input-plus-output tokens are A 187,626; B 78,874; C 79,082; D 0. Task-plus-preflight wait is A 126.104 s; B 112.297 s; C 142.659 s; D 29.764 s. B uses 57.96% fewer all-attempt input-plus-output tokens and has 10.95% lower recorded wait than A. C uses 0.26% more tokens and has 27.04% higher wait than B.

`paired_contrast.py` pairs all 12 block/task rows across arms after checking token, layout, and phase. B is faster than A in 8 of 12 pairs; A is faster in 4. B is faster than C in 10 of 12 rows, while C has three unsuccessful rows. D is faster than B in all 12 rows, but D is a known-form deterministic route; human setup time was not measured. Pairwise results describe this two-block archive and are not population estimates. Its task elapsed values exclude the separately measured schema-preflight waits.

`target_linkage.py` independently checks A's admitted point moves against the archived grounding points and links each executed B/C field or submit move to a prior VALID, eligible alias-target check matching the grounded point and live window. It finds 24/24 A grounding matches and 45/45 executed B/C moves linked (B 24; C 21). This trace linkage does not establish all collateral GUI state or the full physical input-authority chain.

These are retained-record audits. They do not verify the original host, independently reproduce human setup cost, or establish causal/general performance claims. Cached input and reasoning output are subsets of token usage, not additional tokens. No historical arms are pooled.
