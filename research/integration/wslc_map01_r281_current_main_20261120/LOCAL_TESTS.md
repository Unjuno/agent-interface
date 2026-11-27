## Current-main cancellation-release regression

- Repository ref: 381a21ace42891c2cd1e9cff3e231bec763ec2ba (checked against main during this work).
- Test: research/live_control/cancel_release_publication_59/test_cancel_release_publication.py, Git blob 696a72f3583a741c5077dcaebf72cba56d95838a.
- Support files: input_owner_v11.py blob 842071284156d3ccc647f47135ee62a9e512cb56; input_owner_v13.py blob 69fe59c179ea85f189c302ea15866c38dc90a94d. Other imports came from the independently verified R281 current-main source snapshot.
- Runtime: preinstalled WSL venv, Python 3.12.3.
- Normal: 8 tests passed (0.036 s).
- Optimized: 8 tests passed (0.079 s) using python -O.
- Scope: cancellation release publication, delivery failure, at-most-once handling and fail-closed admission. This is not an expiry-specific unit test; R279-R281 cover actual expiry behavior live.
- No repository source was edited.
