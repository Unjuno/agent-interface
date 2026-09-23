# Primary portable key-repeat use (draft evidence)

The primary agent used the portable runtime built from main fb69cac2af4a8f6073a7afe5b54b1c7124bdf3fe in WSL Ubuntu against one owned Xvfb/Tk fixture. No sensor implementation or model delegation was used.

After viewing the empty entry, the agent issued one program: focus/click, type ABCDEF, Left repeated three times, type a hyphen, save, capture, and release. The facade expanded 12 source instructions to 14 operations and retained the source-index mapping. All completed. The returned capture still showed the empty entry. No input was replayed. One additional explicit observation showed ABC-DEF and saved:ABC-DEF; independent effect.json agreed.

The local dispatch process interval was 376.883203 ms, including Python startup and result serialization. It excludes model deliberation, image presentation and the later observation; it is not time to useful feedback or semantic completion. Fixed 50 ms waits did not establish redraw completion. This single trial is not a comparative performance or token result.

The owner exited with code 0 after explicit stop; its two tracked children were reaped. Descendant verification remains false. Source observation and binding numbers were caller supplied, not server-issued authority. Compact review retained receipt-view-v1.

The archive retains the executable, source manifest, scripts, decision/program, raw replies, images, application events/effect, call clocks and cleanup. RESULT.json lists each archived file hash. Existing frozen evidence was not changed. WSL primary-use evidence only; formal container/independent-review adoption gates remain outstanding.

## Post-run source review: fixture overhead is uncontrolled

The source review in `SOURCE_REVIEW.json` pins the fixture and backend files to the same recorded main revision. Each XTEST key/button operation calls `Display.sync()`; this flushes/synchronizes with the X server but does not acknowledge Tk processing or redraw. A missing input flush was not found in those paths.

The fixture logs key/button events synchronously: each Tk callback opens, writes and closes `events.jsonl` in the Windows-mounted `/mnt/c` result directory. Saving also writes its effect file there before updating the label. This is a potential event-loop delay and an uncontrolled factor in this trial. It does not prove that filesystem I/O caused the stale capture. No callback timing, timestamped application-event trace, or logging-disabled comparison was collected.

Therefore the retained observation establishes only that this instrumented fixture's action capture preceded its displayed effect. Do not generalize its delay to ordinary applications or use it to select a universal wait interval. The original 29-file archive and RESULT.json are unchanged; this source review is a later companion, not newly collected live evidence.
