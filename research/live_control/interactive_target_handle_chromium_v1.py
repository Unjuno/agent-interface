"""Chromium fixture using scoped target handles plus optional surface movement."""
import cause_servo_interactive_v4 as implementation
from executor_v4 import Executor
from session_v29 import Backend


implementation.Backend = Backend
implementation.Executor = Executor
implementation.main()
