# Local construction checks

Command: `python -m unittest research.analysis.assay_sensitivity_5850_t0_v1.test_t0`  
Environment: Windows CPython 3.12.  
Disposition: 4/4 PASS. This is construction evidence only; it is not a Docker/formal allocation.

The test-first RED run failed all three initial behavior assertions because `candidate.qualify` did not yet exist (AssertionError, not import or syntax errors). After minimal implementation, all four tests pass.
