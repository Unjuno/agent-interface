"""Run the seed991004 target/guard fixture at a held-out 1280x720 viewport."""
import interactive_l_target_guard_v2 as implementation


OriginalSession = implementation.suite.Session


class TransformedViewportSession(OriginalSession):
    def spawn(self, argv, *args, **kwargs):
        transformed = list(argv)
        index = transformed.index("-r") + 1
        if transformed[index] != "1024x720":
            raise ValueError("unexpected source resolution")
        transformed[index] = "1280x720"
        return super().spawn(transformed, *args, **kwargs)


implementation.suite.Session = TransformedViewportSession
implementation.main()
