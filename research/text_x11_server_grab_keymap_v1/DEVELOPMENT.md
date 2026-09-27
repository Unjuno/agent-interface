# Development record

1. Initial no-grab vs grab matrix showed no-grab reproducing German `"` and French `2`; grab initially produced exact `@` for both.
2. Receipt hardening made the external mutator return its applied-map hash. Repetition then exposed non-determinism: one German grab session and multiple French grab sessions produced wrong text despite `request_start < first_input < ungrab < mutator_sync_done`.
3. Receiver key event logging showed the same keycode 11 interpreted as `at/@`, `quotedbl/"`, or `2/2` across fresh sessions. Key callbacks occurred after ungrab, often before mutator sync completion.
4. A thread-safe receiver shadow was added so semantic state can be queried during server grab without any X request. US, German and French development probes all showed `shadow=""` and zero receiver key events while grabbed, even after owner XTest input had completed. Application text appeared only after ungrab.
5. This separates X-request serialization from application semantic commitment. Stop tuning and freeze a repeated-session semantic-serialization discriminator rather than promoting server grab from a single lucky session.
