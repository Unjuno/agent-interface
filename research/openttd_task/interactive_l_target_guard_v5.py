"""Run seed991004 at 1152x720 with runtime-resolved framed pointer intents."""
import interactive_l_target_guard_v2 as implementation
from executor_v4 import Executor
from session_v26 import Backend


OriginalSession = implementation.suite.Session


class FramedIntentSession(OriginalSession):
    def spawn(self, argv, *args, **kwargs):
        transformed = list(argv)
        index = transformed.index("-r") + 1
        if transformed[index] != "1024x720":
            raise ValueError("unexpected source resolution")
        transformed[index] = "1152x720"
        return super().spawn(transformed, *args, **kwargs)


implementation.suite.Session = FramedIntentSession
implementation.Backend = Backend
implementation.Executor = Executor
implementation.main()
