# A02 first-audit diagnosis

The frozen auditor exited 2 and its first report classifies the allocation `FAIL_METHOD`, as required by the preregistered integrity gate. This is an auditor reconstruction defect, so the experiment does not support a scientific conclusion about interval TTC.

All 98 reconstruction mismatches are in the `occlusion` profile: 49 point estimates and 49 intervals. The candidate scores each prefix using only observations available at that prefix. In contrast, `independently_estimate()` checks the entire future history for two consecutive missing radii before iterating over prefixes (`auditor.py` lines 21–23). Thus the later occlusion makes the auditor expect UNKNOWN even on earlier prefixes where the candidate only had valid observations. This violates the intended prefix-by-prefix comparison.

The raw candidate and first auditor report are preserved unchanged. Candidate ran once (exit 0); auditor ran once (exit 2); retries are zero. The auditor is not rerun, and these outputs are not relabeled as a method result. A corrected auditor would require a separately frozen successor allocation and authorization under the issue's one-shot constraint.
