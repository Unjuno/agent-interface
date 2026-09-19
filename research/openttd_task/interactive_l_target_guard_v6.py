"""Run seed991004 with the post-admission binding-change fault backend."""
import interactive_l_target_guard_v2 as implementation
from executor_v4 import Executor
from session_v27 import Backend


OriginalSession = implementation.suite.Session


class BindingFaultSession(OriginalSession):
    def spawn(self, argv, *args, **kwargs):
        transformed = list(argv)
        index = transformed.index("-r") + 1
        if transformed[index] != "1024x720":
            raise ValueError("unexpected source resolution")
        transformed[index] = "1152x720"
        return super().spawn(transformed, *args, **kwargs)


implementation.suite.Session = BindingFaultSession
implementation.Backend = Backend
implementation.Executor = Executor
implementation.main()
