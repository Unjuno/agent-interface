# Post-STOP construction diagnostic (not a formal rerun)

The pinned image reported `Inkscape 1.2.2 (b0a8486541, 2022-12-01)`. Recreated an isolated Xvfb display with the same Xauthority cookie setup as the formal runner, then invoked its exact Inkscape command with stderr captured. The process exited and stderr was:

```text
Unknown option --no-splash
```

The runner command was `inkscape --no-splash --new`. This confirms the first unsupported option as a sufficient explanation for the missing Inkscape window; this was a post-STOP construction diagnostic and did not change or repeat the formal allocation. A fresh successor (#3649) will use the bare, already construction-tested `inkscape` command and independently preregister the change.
