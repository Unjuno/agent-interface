# Excluded construction record

Construction-01 exercised six cases and produced the intended candidate outcomes, but the independent auditor's copied-evidence `drop_row` control did not reject because the construction denominator was not checked. It returned 7/8 corruption controls. **No formal case ran.**

The only source change was `audit.py`: add an exact denominator check for construction mode (6 rows), while retaining formal denominator 18. Construction-02 then completed 6/6 cases, all producer/relay exits 0, candidate outputs matched the declared scenario table, policy units passed 5/5, audit errors were empty, and all 8/8 corruption controls rejected. This is construction eligibility only, not scientific evidence.
