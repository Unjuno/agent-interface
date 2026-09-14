"""Run seed991004 with scoped target handles and a between-use surface move."""
import interactive_l_target_guard_v2 as implementation
from executor_v4 import Executor
from session_v29 import Backend


OriginalSession = implementation.suite.Session


class TargetHandleSession(OriginalSession):
    def spawn(self, argv, *args, **kwargs):
        transformed = list(argv)
        index = transformed.index("-r") + 1
        if transformed[index] != "1024x720":
            raise ValueError("unexpected source resolution")
        transformed[index] = "1152x720"
        return super().spawn(transformed, *args, **kwargs)


implementation.suite.Session = TargetHandleSession
implementation.Backend = Backend
implementation.Executor = Executor
implementation.main()
