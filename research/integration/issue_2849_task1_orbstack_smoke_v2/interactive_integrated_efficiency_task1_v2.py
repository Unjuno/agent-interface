"""Existing checked-input runtime with the additive task-1 fixture adapter."""
import cause_servo_interactive_v4 as implementation
from executor_v4 import Executor
from session_v33 import Backend

import integrated_efficiency_runtime_task1_v2 as integrated

implementation.suite.prepare = integrated.prepare
implementation.suite.evaluate = integrated.evaluate
implementation.Backend = Backend
implementation.Executor = Executor
implementation.main()
