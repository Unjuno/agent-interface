# Native MCP desktop use and continuation guidance

Three completed private Docker allocations exercise the existing native MCP
entry path with primary-agent decisions. Two Calc runs saved the requested
values and verified input release; the Inkscape run was refused before input
after the displayed layout changed. All outcomes are retained together.

## Calc: use the continuation already delivered

Both Calc runs used seed991283, Calc25.2.3, the same Docker image, text gap2ms,
two input requests, and explicit250ms waits. The primary entered A1=763/A2=660,
viewed and accepted the Excel-format dialog, then explicitly finished. Each
saved workbook was read separately after the primary visible-goal declaration;
both contained 763/660. Input release was verified for both actions in each run.

Both action replies had `feedback_status=needs_review`, while `image_status=image`
and `continuation.status=source_available` provided the next viewed source. A
dialog's `BadWindow` feedback remained recorded. This is not a clean feedback
PASS. The next stage/source identities were already present in each response.

In calc-01 the primary additionally read source-2.json/source-3.json for those
identities. In calc-02 it used the delivered continuation directly. The new
native_submit discovery wording and documentation explain that existing path;
no execution, image validation, guard, retry, or wait policy changed.

| First-submit through finish-return | calc-01 | calc-02 |
| --- | ---: | ---: |
| Total client span, seconds | 72.653278 | 74.639052 |
| Inside three SDK calls, seconds | 1.813533 | 1.950276 |
| Between calls, seconds | 70.839745 | 72.688775 |

**No speed improvement was observed.** The successor was about1.99s longer.
This is an ordered pair of primary uses, not a randomized or replicated causal
estimate. Between-call time combines host tools, presentation, deliberation and
request assembly. Extra source reads shared existing shell calls; eliminating
them did not remove MCP calls or establish fewer outer tool turns. Setup, final
status checks and saved-file readback are outside the table. Model input tokens,
isolated interpretation time, first useful feedback and human comparisons remain
unmeasured. Do not present this as a matched performance PASS.

## Inkscape: preserve the refusal

The seed991284 goal requested moving the red rectangle right while preserving
SVG geometry. The initial image showed a rectangle around screen x514..641;
the retained pre-admission image showed a Fill and Stroke sidebar and the
rectangle around x310..417. Cause of that layout transition is unproven. The
explicit first request was refused with `region_pixels_missing` / `MISSING`,
`input_dispatched=false`. No input was replayed. No response image or next-stage
continuation was available, and no saved-goal success was obtained.

The owner exited1. Its cleanup report records tracked processes terminal but
does not verify all descendants. The SDK client/container exited0 after closing;
that is not application-task success. The failed attempt to display an absent
action-1.png was followed by inspection of its refusal metadata. No image was
substituted as a successful response.

The current setup predicate detects a visible red target; it does not promise a
stable layout. This result does not justify relaxing guards or adopting the
unrelated scoped GTK temporal-stability fixture as an Inkscape readiness policy.
The intended next check uses the existing input-free observe/review operation
on a fresh allocation before choosing new input. It has not run in this bundle.

## Provenance and inspection

Image: `sha256:44634c6599b9713b382da9937db38d409c9e66bcbce95aaf2bfeae7793c11385`.
The environment directory retains the Dockerfile, build log, import/program
preflight, package versions, and initial missing-dependency error. It was built
from cached local images and repository packages, not a published fully pinned
image recipe. Network was disabled during the live allocations. No host display,
Docker socket or credentials were mounted into them.

Source recorded before use: calc-01 `6e4ba70e6471f002a902812bf8b66637e028cc50`;
calc-02/inkscape-01 `19909111c6c58394cb892f9b0be9f7d9d9387c97`. The checkout was
mounted read-only, without a separate frozen source snapshot; no implementation
edits occurred while an allocation was live. This is SDK-mediated use, not a
host-registered call. No secondary agent or new sensor was used. Calc owner exits
are recorded0; client/container0 was inspected after closure, while full
descendant cleanup remains unverified.

The archive contains every file from these three allocation directories and the
environment directory. Paths inside responses refer to the original allocation.
The Inkscape RESULT.md was written after C: storage recovered; its first write
failed at zero free bytes. It is explicitly a reconstructed memo, not pre-run
evidence. Raw responses/images preceded the storage incident. JSON parse checks
alone were not taken as a full integrity audit.

Run `python runtime/results/native-desktop-continuation-01/verify.py` from the
repository root to check archived bytes, task/release records, continuation
identity use and timing arithmetic. It reads without extraction or execution.
It does not repeat the apps, independently evaluate all pixels, or close the
six-task integration spine. Keep both the slow successor and failed Inkscape use
when assessing these results.
