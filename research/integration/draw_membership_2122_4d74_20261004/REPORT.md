# B03: live-page reference equality qualifies replacement refusal

Successor experiment for Issue #2122, B02 (PR #7334). Original B02 failure and B01 success are unchanged.

H: comparing a retained original UNO reference with freshly enumerated live page references may distinguish a removed original from a matching replacement.

T: one actual WSLc container invocation; four fresh Draw documents ordered positive_0, replacement_0, replacement_1, positive_1. An independent UNO process moves A/B to x=1700/2700 and in replacement cases removes A, inserts a distinct A with matching visible fields, and restores page order. Candidate keeps the original reference. It requires the previous visible-state guard AND exactly one equality match against page.getByIndex references. Fixture titles are excluded from admission.

D: first frozen saved-state auditor exit0, errors[], SUPPORT_REPLACEMENT_REFUSAL_SCOPED. Producer/container exit0/errors[]. Both ordinary controls yielded equality [true,false], admitted one setter, and saved A1900/B2700. Both replacements yielded [false,false], refused with zero setter calls, and saved generation1 A1700/B2700. Independent observer and saved XML agree. No replay or regrade of B02.

C: image sha256:bab4dc0dff6ffa8270e86873c3987e0e3203c1b198a08ff971580a6c04c3ba1d; CPU1, memory512MiB, networknone, user65534:65534, source mounted read-only, output writable. Root filesystem is not claimed read-only. No model calls.

U: this qualifies equality-based membership at the measured boundary only. It does not prove universal native identity, authenticated generation, ABA safety, atomic admission, protection against a writer after enumeration, or model value. Titles are scorer-authored provenance, not runtime identity credentials. The auditor is byte-identical to B02 and evaluates saved effects/refusal; it does not itself verify equality vectors. Those vectors must be checked against RAW.json and the frozen controller during independent publication review. No production adoption or Issue closure follows from this result.

Evidence: six sources frozen before execution, including literal source-B02-app.py; raw results, four FODG files, separate writer/observer outputs and original logs retained. Publication FILES.json covers all copied members; publication README, FILES.json and .gitattributes are outside the manifest. Namespace attributes preserve original bytes.

First result: https://github.com/Unjuno/agent-interface/issues/2122#issuecomment-5975065201
