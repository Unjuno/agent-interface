# Startup factory failure and journal retirement

The synchronous client opens an exclusive UTF-8 journal before calling its
process factory. When that factory raises, the constructor attempts to close
the journal before propagating the same startup exception. This includes
BaseException, so interruption does not skip the attempt. A failure in
journal.close is exposed as the cause of the original startup exception;
that resource retirement is incomplete and must not be reported as success.

This change surrounds only process_factory. It preserves the strict UTF-8
stdio, binary stderr drain, active response ownership, request, notification,
journal and normal close behavior inherited from the submitted client bundle.
It does not provide cleanup for failures after a process has been returned,
such as reader-thread startup failure, or a hard overall close deadline.

The new startup unit module uses injected prelaunch exceptions and real owned
journal handles. It checks missing-executable error, general OS error,
interruption, no-journal control and cleanup-error chaining. No OS peer,
provider, GUI or protocol request is launched by those five cases.

Separate ordinary Windows backend qualification used real Popen/CreateProcess
refusals for an absent executable and nonexistent cwd. The original source
retained an open journal and its rename failed with sharing WinError32; the
repaired source closed it, allowed the rename and preserved the same original
WinError2/267 exception. No returned process handle is not an all-descendant
absence certificate. First failed injected regressions and all backend rows
remain evidence outside the approved source tree, under the parent #57 work.

These are resource-boundary repairs and scoped regressions. They do not prove
physical input release, actual model/task effects or improved total resource
cost. Earlier content votes do not approve this changed source. Integration
requires a fresh proposal and reviews, then actual current-base applicability,
ownership/cancellation and platform/one-sender conditions under FINAL-v5.
