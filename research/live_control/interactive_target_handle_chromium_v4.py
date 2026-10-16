"""Chromium fixture with combined fresh observation and target-alias check."""
import cause_servo_interactive_v4 as implementation
from executor_v4 import Executor
from session_v32 import Backend


implementation.Backend = Backend
implementation.Executor = Executor
implementation.main()
