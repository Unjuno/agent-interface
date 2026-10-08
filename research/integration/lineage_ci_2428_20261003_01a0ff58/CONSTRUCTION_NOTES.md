The actual new workflow command ran once and exited0, as did the focused
optimized command and unchanged compile command. No ordinary check repair or
historical source/auditor replay was needed.

A later read-only log inspection used a Windows wildcard as an rg literal path
and called git ls-remote from the projectless directory. Both inspection steps
errored; the preceding log read succeeded. This did not invoke any test or
publish/send anything. The inspection was repaired with rg -g on the actual
directory and Git's explicit owned repository cwd. Original tool output remains
in private task history. No standalone command UTC/stream receipt was captured
for this inspection error, and none is invented.

Further read-only source inventory queries guessed two nonexistent core module
names and two nonexistent private evidence directories. Those reads emitted
missing-path diagnostics. They were replaced by actual rg --files/Get-ChildItem
inventories and explicit Git-tree paths. Valid preceding source/diff reads remain;
no test, doctor, historical fixture or publication was repeated for these errors.
No standalone native receipt was captured for those inventory queries.

First staged default Git whitespace inspection reported Windows CRLF as trailing
whitespace in newly retained receipt/stream bytes. Its individual native exit
was not captured separately: the shell continued to the local commit, so the
overall native exit0 reflects that later commit, not successful whitespace
inspection. Local construction commit744b3ee352 is retained in Git history
(the marker is an abbreviation). No runtime test/doctor/raw was rerun or
normalized. Actual attributes for this new archive were unspecified; local
core.autocrlf=false alone was not a portable byte-preservation rule. A separate
explicit Git whitespace inspection with cr-at-eol accepted the retained Windows
line endings and exited0. The repair adds archive-local .gitattributes with
* -text and the normal blank-at-eol/blank-at-eof/space-before-tab checks plus
cr-at-eol. This applies only to its artifact subtree, preserving exact bytes on
other checkouts and allowing expected Windows line endings. The first default
inspection remains a failed historical check; subsequent check results are
separate. Retained source/receipt/stream hashes stay exact.
