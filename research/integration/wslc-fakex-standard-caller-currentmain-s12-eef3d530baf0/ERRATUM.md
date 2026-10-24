# S12 setup erratum

S12 started one isolated WSLc session and one no-network container, then stopped during offline dependency installation before the unittest body ran. The container runner reported CPython **3.12.14**; S12 had mistakenly frozen CPython 3.14 wheels based on an incorrect reading of the image record. The target wheel `pydantic_core==2.50.1` was incompatible with the image interpreter, so the test did not start. No behavioral result is claimed.

Cleanup receipts report the exact container deleted, pinned image deleted from the isolated session, and the named WSLc session terminated. The S12 allocation is consumed and will not be rerun. S13 uses a fresh unique session/container and a CPython 3.12 wheelhouse; any S13 failure is retained without retry.
