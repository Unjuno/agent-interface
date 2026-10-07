"""Chromium fixture with read-only target-handle query and admission revalidation."""
import cause_servo_interactive_v4 as implementation
from executor_v4 import Executor
from session_v30 import Backend


implementation.Backend = Backend
implementation.Executor = Executor
implementation.main()
