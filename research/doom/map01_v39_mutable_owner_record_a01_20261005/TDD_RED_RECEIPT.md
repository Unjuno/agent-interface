# TDD RED receipt

Merged PR #7832 already preserves the container baseline RED and diagnostic neutral-state revisit; this packet does not claim first discovery. The first local semantically valid regression run used the unmodified PR #7805 candidate bridge at commit `311f834bf63111b344297f947f8546128c7a1844`. At the aggregate-query barrier, the owner had appended one record with `verified=false` and no aggregate `keys_down`; the bridge drain advanced `_owner_record_cursor` to 1 and retained `{'F8'}`. After unblocking reconciliation, that same record became `verified=true` and `keys_down=[]`; the next drain still retained `{'F8'}`.

The intended RED assertion failed exactly:

```text
AssertionError: Items in the first set but not the second:
'F8' : bridge kept F8 after same owner_release record became verified-empty
```

Two earlier attempts stopped before the semantic assertion: one patched an instance rather than the `Root` class used by the fixture; the next used an incompatible bound-method signature. Both were corrected and are not counted as RED evidence. The successful RED above is the retained TDD baseline. The predecessor bridge blob is pinned in `SOURCE_LOCK.json`.
