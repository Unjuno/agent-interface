# Issue 3935: preformal source-publication STOP

**Disposition: `STOP_SOURCE_PUBLICATION_BLOCKED`. Formal invocations: 0.**
The planned 48-case formal experiment was not run. Construction is excluded and
is not a formal PASS. This record does not close #3935, #57, #732 or ROADMAP.md.

## Lineage and scope

Successor to closed #1564's spatial tiny-change study. Intake/main anchor:
`b2457b746a6df06f6536585dfe2ab937aff639f4`. The predecessor's result and production
O1 implementation are unchanged. Relevant open/closed issues, open PRs and 62
returned branch entries were inspected. No existing XDamage study was found.
The work is separate from #2692 receipt transport, #3876 passive reading and
#3929 query-version work. Only this additive documentation path is integrated.

## H / T / D / C / U

**H:** Exact endpoint equality does not establish that nothing happened between
captures. A drawable may change A -> B -> A while O1 correctly suppresses the
identical endpoint. XDamage NonEmpty may retain drawing evidence, but an
identical repaint may also notify. Such a hint cannot recover semantic history
or grant input authority.

**T:** The unexecuted formal plan is eight fresh private Xvfb sessions with six
fresh 64x64 windows each, rotating QUIET, REPAINT_A, PERSIST_B, ABA_1PX, ABA_2X2,
ABA_8X8. A separate renderer process performs native core X11 drawing; an
observer connection watches damage, and another connection captures actual RGB
frames. XSync barriers place the middle change between endpoint captures. Only
the endpoints reach the unchanged ExactGate/Receiver. Middle frames are an
independent evaluator input, not candidate information. No mouse/keyboard API,
model, external network, real task or user desktop is used.

**D:** Before one formal invocation, exact source publication and readback were
required. All 48 cases, source/byte/process identities and independent audit
would then have to reconcile, including 12 finite evidence mutations. That
publication gate was not completed; formal count remains zero.

**C:** Barrier-authored transients are not natural event-miss frequencies or a
latency benchmark. Damage can coalesce or over-report drawing. No semantic
content, number of transitions, changed-pixel region, general GUI coverage,
token saving or task benefit follows from a notification.

**U:** Event loss/reconnect, capture/acknowledgement races, semantic critical-event
retention, GPU/compositor/Wayland coverage and matched model/task usefulness
remain untested. Broad research goals remain open.

## Excluded construction evidence

Two separate six-case construction invocations completed. They are not pooled.
Construction-01 used native ctypes bindings after discovering that the installed
Python-Xlib package lacks DAMAGE support and distribution metadata. The initial
ImportError and metadata lookup failure were setup observations, not experiments.
No dependency was installed. The initial local ExactGate copy had an extra final
LF; it was corrected and verified before any live construction to match Git blob
`d2629bc94d40cc0a8e1bf9e053585549218629ed`.

Construction-02 used Python `-S`, added actual executable identity receipts and
stricter independent type/command checks. Its results were:

| Case | Different middle | Different endpoint | O1 forwards endpoint | Interval damage |
| --- | --- | --- | --- | --- |
| QUIET | no | no | no | no |
| REPAINT_A | no | no | no | yes |
| PERSIST_B | yes, 8x8 | yes | yes | yes |
| ABA_1PX | yes, 1 pixel | no | no | yes |
| ABA_2X2 | yes, 2x2 | no | no | yes |
| ABA_8X8 | yes, 8x8 | no | no | yes |

This is one row per condition, not eight replications. Native renderer and Xvfb
both exited 0 with empty stderr. The raw-only audit reported zero errors and
12/12 evidence mutations were rejected; eight malformed/coverage controls
returned UNKNOWN with authority false. These are finite construction checks,
not independent human review or proof of arbitrary auditor soundness.

Environment: supplied Linux x86_64 execution container, CPython 3.13.5, installed
Xvfb/libX11/libXdamage. Docker CLI was absent. No Docker/OrbStack image identity
or engine equivalence is asserted. Xvfb used a fresh display, no TCP listener,
fixed 24-bit screen and `-ac`; this is not an authenticated production deployment.

## Integrity identifiers

- Construction-01 raw: 36,054 bytes, SHA-256
  `e688ba5b92a4670a013fe01e303b1ec9df6ce80148b09f3df24f19adef3fd487`.
- Construction-02 raw: 22,145 bytes, SHA-256
  `5b513ee76a3eea70a666ec47937c9fd0e3867eb159159bb7d14edd69527ebbb6`.
- Local source/environment freeze, not a formal receipt: SHA-256
  `7a4228e660cd1a29123ade59339c314c0861fda6a2ee7ad247acc27dbaa4f938`.

## Exact stopping reason

A source-archive upload returned Git blob
`c236e7b43475d5c038c6009fd1e69804ca14cde2`, not the local expected blob
`ddbdfceaf4d05ee40f09f7b41ec9137c1cb2e581`. The mismatched blob was not attached to
a branch, trusted or executed. The connector rejected its readback as non-UTF-8.
A subsequent readable source-tree upload was explicitly blocked by the tool's
safety check. No alternative source-upload route was attempted after that block.
This is a publication/setup failure, not evidence against the scientific H.

Only this STOP report is in the PR. Complete source and raw data are **not**
claimed to be on GitHub/main. A separate local data-only handoff retains the two
raw construction records, latest raw-only audit/mutation receipts and hashes;
it excludes the blocked source payloads. It is not a complete reproducibility
package without the corresponding source.

## Roadmap disposition

Intake and excluded construction are complete. Remote source freeze/readback is
blocked. Formal allocation, formal audit, source/evidence integration and
scientific closure remain unperformed. This documentation PR preserves the
boundary and stopping reason; it does not satisfy those remaining stages.
Other agents' branches and evidence are untouched. Own-branch cleanup is allowed
only after this report is verified on main and dependent PRs are absent.
