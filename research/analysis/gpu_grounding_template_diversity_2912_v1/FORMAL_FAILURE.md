# Issue #4546 — pre-training construction STOP

**Disposition: `STOP_CUDA_DETERMINISTIC_ADAPTIVE_POOL_BACKWARD`.** This is a retained pre-training construction failure, not a scientific result and not evidence for or against the template-diversity hypothesis.

The mandatory deterministic CUDA backward gate failed with the frozen local PyTorch 2.5.1+cu121 stack. The full TinyGrounder and a minimal adaptive-average-pooling operator both reported that `adaptive_avg_pool2d_backward_cuda` has no deterministic implementation. Forward shape was `[16,2]`. Strict determinism, cuDNN deterministic mode, TF32 disabled, and `CUBLAS_WORKSPACE_CONFIG=:4096:8` were in force.

Formal invocations: 0. Optimizer steps: 0. No corpus was rendered, no arm was trained or evaluated, and no hypothesis decision was produced. Earlier #4482 evidence remains unchanged. No pooling substitution, determinism override, dependency upgrade, retry, GUI/input action, or runtime promotion occurred.

Environment, exact failure text, pre-registration, freeze, checksums, independent integrity audit and corruption tests are retained alongside this file. Docker GPU visibility was verified with the installed CUDA diagnostic image; the operator failure was evaluated on the already-installed host CUDA stack under the host fallback explicitly allowed by Issue #4546. The compatible PyTorch GPU container image was not cached and registry retrieval stalled.
