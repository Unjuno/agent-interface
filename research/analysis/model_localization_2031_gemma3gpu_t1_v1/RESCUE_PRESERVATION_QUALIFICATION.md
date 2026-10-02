# Rescue preservation and provenance qualification

This note accompanies PR #6639 at reviewed rescue head `10d540e073032e2be5e993e867fb1ce654274270`. All 117 rescue-package blobs remain unchanged by this integration. Of those, 115 match the original #6378 package blobs; the rescue README and REPORT already contain the author's integrity qualifications. Candidate source, raw request/response/record files, audit output and images were not regenerated or amended here.

## Historical hash-audit attribution

The rescue README/REPORT quote the author's earlier 113/114 manifest comparison and REPORT digest `2b35b838…05437` versus expected `1bbd2132…abd90`. These are historical reported audit findings, not a new digest verification by this review. The rescue adds text to REPORT: original #6378 report blob `ab08dcd6cbadc8e70c0b2a65e18cff1747a1b68f` differs from the reviewed rescue report blob `7fc576563601f470645c5bc9cb846474d2408e87`. Do not treat the repeated historical digest as an independently established digest of the newly qualified report text. The original contemporaneous report bytes matching the manifest remain unavailable; no replacement hash or reconstructed original is supplied.

## Unchanged scientific and execution limits

The artifact-integrity HOLD, one-invocation auditor-cap deviation and response-schema/scorer mismatch all remain controlling. The retained 1/8-per-arm table is not a valid pure localization-accuracy estimate. Original candidate observations and diagnostic audit are retained without re-scoring, and no formal all-gates PASS, useful crop benefit or runtime/product promotion is established. The initial auditor failure remains described in the task/Issue history; this review does not create or claim custody of missing execution transcripts.

This review inspected repository scope, source/scoring logic, documented limitations and Git-blob custody. It did not revalidate every raw/image semantic result, execute a model/candidate/auditor/test, regenerate images or recompute SHA-256 values. The 12 unrelated generated-index links removed by the initial rescue diff are preserved from current main; the only resulting index change is this package's link. The historical failed Analysis Index check is not relabeled as passed.

Issue #2031 remains open. Closing original #6378 as superseded did not establish a scientific PASS or resolve its remaining model-utility question.
