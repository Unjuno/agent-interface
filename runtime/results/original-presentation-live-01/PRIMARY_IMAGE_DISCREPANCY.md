# Preserved primary image-reading/presentation discrepancy

Primary first viewed primary-001.png and read READY. The first views of
primary-005.png (immediate input) and primary-007.png (re-presented original)
appeared all black to the primary. The input review records that apparent
discrepancy and explicitly declines to call native pixels black or Save complete.
The original input was not replayed.

After explicit close and terminal owners, the same files had identical SHA256
3f3535bb712285e350d6df1952c8ff48197ea160aa8d7acc84309b0aa47c1986.
PIL decoded each with RGB extrema 0..255, so they are not all-black files.
The same unchanged primary-007.png was viewed again after the terminal oracle;
READY was visible. The post-cleanup emission forwarded image detail original
explicitly; earlier emissions used the helper's default. Source bytes were not
edited/replaced and no native capture was repeated for that re-view.

Source identity, delivery option, context and perception must be distinguished.
This case does not isolate the cause or prove that the detail option fixes it.
The discrepancy remains an unsuccessful first-view outcome, not an image-capture
corruption claim, successful visual correction policy or population result.
The re-presentation primitive preserved historical pixels but did not, in its
first primary view here, resolve the visual ambiguity. A separate fresh source 7
was viewed as SAVED and only then attributed as visible completion.


## Exact tool-image handoff retained

actual-source-records.jsonl retains only the 39 original tool-input/tool-output/
usage rows used by this case projection, with original source line numbers and
raw line bytes. No reasoning or other conversation records are included.
verify_retained_source.py replays their original hashes, usage counters and input
boundaries offline, without the full private session log. Normal and -O runs
pass and reject missing, duplicated and byte-modified source records.

The five encoded image blocks in those exact tool outputs match the saved native
PNG bytes: READY for views 1, 2, 3 and 5, SAVED for view 4. Their emitted detail
values were high, high, high, original, original. Earlier view_image requests
specified original, but the outer image emission omitted forwarding that detail;
the later emissions forwarded it explicitly. The first high-detail view already
showed READY correctly, so this sequence does not establish a causal detail fix.
Provider preprocessing and model perception are not independently observed.
The initial black-image reviews remain unchanged, and no live case was rerun.
