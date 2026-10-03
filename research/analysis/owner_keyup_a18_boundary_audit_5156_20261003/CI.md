# Local validation

The scoped regression passed its unchanged retained control and all ten negative
subcases after eight expected red failures. C01 candidate and independent auditor
each exited 0 in pinned WSLc; source hashes remained unchanged after the run.
The analysis index checker passed in sparse mode after adding one sorted entry;
workspace `--git-tree` inventory passed (156 top-level directories). These are
local checks, not a hosted-CI result.

The broader existing command
`python -B -m unittest discover -s research -p 'test_*workspace*.py' -v`
ran 21 tests on Windows and reported nine errors across six test methods:

- `test_current_default_fallback_without_git_is_preserved`: WinError 5 removing
  read-only Git objects in its temporary fixture.
- `test_missing_root_and_git_error_fail`: same fixture removal error.
- `test_hidden_regular_nested_unicode_and_tab`: WinError 123; tab is invalid in a
  Windows directory name.
- `test_document_symlink_rejected`: WinError 1314; symlink privilege unavailable.
- `test_hidden_symlink_ignored`: same symlink privilege error.
- `test_symlink_entries_fail_closed`: four target subcases report the same
  symlink privilege error.

These existing fixture/environment failures were not suppressed or treated as
passing. Linux equivalents of that broader suite have not been run for this
proposal. No workspace checker, tests, workflow or runtime was modified. A later
Git preparation attempt also encountered host memory exhaustion; the research
outputs had already exited successfully and were preserved unchanged.

The frozen C01 candidate, auditor and wrapper have not been rerun. Hosted checks
and FINAL-v5 review/apply gates must be verified independently at integration.
