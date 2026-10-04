"""Checked session_v33 runtime over the six-task comparison fixture."""

import cause_servo_interactive_v4 as implementation
from executor_v4 import Executor
from session_v33 import Backend

import integrated_efficiency_runtime_v1 as integrated


implementation.suite.prepare = integrated.prepare
implementation.suite.evaluate = integrated.evaluate
implementation.Backend = Backend
implementation.Executor = Executor
implementation.main()
