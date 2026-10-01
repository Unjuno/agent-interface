
The first remote core-only job at source9dca02d1 failed two imports because its
sparse checkout excludes research and distribution modules. Its macOS job log
is preserved in initial-core-ci.log. Split compatibility and archive tests into
their respective layers without changing the runtime. The final core-only
checkout passes56 tests with no research or distribution tree, and split-ci
again passes366 protocol/157 harness checks. The22 focused tests also pass -O
after separation. This test-layout failure is not a GUI or model allocation.
