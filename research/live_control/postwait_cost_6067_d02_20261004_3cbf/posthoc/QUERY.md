# Posthoc query (read-only; not official diagnostic auditor or acquisition)

Source query, evaluated on every retained native-raw/cells/*/source.json:

```jq
. as $root | {cell:(input_filename|split("/")|.[-2]),pid,treatment,events:[.events|to_entries[]|.key as $i|.value as $e|$root.wait_traces[2*$i] as $w|{id:$e.id,delay_ns:($e.draw_start_ns-$w.wait.return_ns),wait_lateness_ns:($w.wait.return_ns-$e.onset_ns),trial_wall_ns:($w.trial.end_ns-$w.trial.begin_ns),trial_process_cpu_ns:($w.trial.process_cpu_after_ns-$w.trial.process_cpu_before_ns),trial_thread_cpu_ns:($w.trial.thread_cpu_after_ns-$w.trial.thread_cpu_before_ns),snapshot_wall_ns:(if $w.post==null then 0 else $w.post.end_ns-$w.post.begin_ns end),exposure_ns:($e.clear_start_ns-$e.draw_end_ns)}],snapshots:[.wait_traces[]|(.pre,.post)|select(.!=null)|{begin_ns,end_ns,cpu_read_begin_ns,cpu_read_end_ns,cpu_stat}]}
```

Capture query, every corresponding capture.json:

```jq
{cell:(input_filename|split("/")|.[-2]),pid,frames:[.frames[]|{index,due_ns,start_ns,native_return_ns,extracted_ns,decoded}],snapshots:[.frames[]|(.pre,.post)|{begin_ns,end_ns,cpu_read_begin_ns,cpu_read_end_ns,cpu_stat}]}
```

Within each treatment's six pulse cells, pool48 event values. Median = sorted
middle value, or mean of the two middle values for even count. Pair differences
= full cell-median minus minimal cell-median. Trial wall minus bracketed thread
CPU is residual WALL only, not syscall/OS descheduling attribution. Control
events are counted but excluded from pulse contrast. Snapshot first/last leaf
counters are global native-container observations, not per-wait absence proof.
Frozen decision remains>=500000ns pooled AND>=5/6 qualifying pairs; no tuning.
