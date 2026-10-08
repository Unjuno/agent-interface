# B05: controller notification lock does not exclude the writer

Issue #2122 successor to B04 (#7343), whose first failure remains unchanged.

H: XModel.lockControllers suspends display notifications and may not exclude an independent UNO writer from the admission/setter gap. The current SDK documents display-notification suspension: https://api.libreoffice.org/docs/idl/ref/frame_2XModel_8idl_source.html . This current documentation is not asserted to be exact source for the pinned LibreOffice binary.

T: one actual WSLc invocation, four fresh documents positive_0, replacement_0, replacement_1, positive_1. An ordinary independent writer first moves A/B to x1700/2700. Controller lock is then acquired before visible-state and live-membership guards and held through the setter. Both replacement cases schedule a second independent writer after admission: it removes original A, creates a distinct generation1 A with matching fields and restores order. It reports controllers_locked=true. The controller uses prior admission, then releases its controller lock before observation/save.

D: first unchanged frozen auditor exit1, FAIL_OR_HOLD, exactly two replacement admission errors. Producer/container exit0/errors[]. All controller rows report locked=true before guard/after setter and false after release. Both late writers complete actual replacement while independently observing the lock. Replacement rows still invoke one stale setter despite required zero-setter refusal; independent observer and saved XML retain generation1 A1700/B2700. Both ordinary controls save A1900/B2700. All guards passed. No retry or regrade.

C: image sha256:bab4dc0dff6ffa8270e86873c3987e0e3203c1b198a08ff971580a6c04c3ba1d, CPU1, memory512MiB, networknone, user65534:65534, read-only source mount/writable output. No model calls. Root filesystem is not claimed read-only.

U: the measured notification lock does not exclude external UNO changes or make admission/effect atomic. This does not prove that no other atomic API or in-process extension can exist. Stop treating notification locks as transaction locks, and stop further generic wait/proxy controls. Next work should qualify authoritative conditional effect or an explicitly weaker post-effect failure/recovery contract. No model value, universal native identity, generation credential, spontaneous race rate or production safety claim.

Evidence: six pre-run frozen sources including literal B04 controller; original raw logs, four FODG documents, initial/late independent writer and observer outputs. The unchanged auditor checks saved effect/refusal; lock state and interleaving require independent source/raw review. FILES.json covers copied members; publication README, FILES.json and .gitattributes remain outside its manifest. Namespace attributes preserve bytes.

First result: https://github.com/Unjuno/agent-interface/issues/2122#issuecomment-5975134370
