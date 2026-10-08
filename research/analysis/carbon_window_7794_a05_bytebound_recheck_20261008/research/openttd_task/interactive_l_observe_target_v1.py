"""Run seed991004 with combined observe-target and existing target/guard semantics."""
import interactive_l_target_guard_v2 as implementation
from executor_v4 import Executor
from session_v32 import Backend


implementation.Backend = Backend
implementation.Executor = Executor
implementation.main()
