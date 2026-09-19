"""Chromium fixture with fresh point-derived target minting."""
import cause_servo_interactive_v4 as implementation
from executor_v4 import Executor
from session_v33 import Backend


implementation.Backend = Backend
implementation.Executor = Executor
implementation.main()
