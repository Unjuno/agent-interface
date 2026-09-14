"""Run the guarded L task with delayed-hover point-target support."""
import interactive_l_target_guard_v2 as implementation
from executor_v4 import Executor
from session_v34 import Backend


implementation.Backend = Backend
implementation.Executor = Executor
implementation.main()
