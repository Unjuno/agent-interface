"""Run the guarded L task with model-point target support from session v33."""
import interactive_l_target_guard_v2 as implementation
from executor_v4 import Executor
from session_v33 import Backend


implementation.Backend = Backend
implementation.Executor = Executor
implementation.main()

