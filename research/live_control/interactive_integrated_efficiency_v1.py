"""Checked session_v33 runtime over the six-task comparison fixture."""

import json
import os
import sys

import cause_servo_interactive_v4 as implementation
from executor_v4 import Executor
from session_v33 import Backend

import integrated_efficiency_runtime_v1 as integrated
from native_comparison_arm_x11_v1 import CONTEXT_ENV, guarded_session


implementation.suite.prepare = integrated.prepare
implementation.suite.evaluate = integrated.evaluate
implementation.Backend = Backend
implementation.Executor = Executor
if CONTEXT_ENV in os.environ:
    output = sys.argv[sys.argv.index("--out") + 1]
    implementation.suite.Session = guarded_session(
        implementation.suite.Session, json.loads(os.environ[CONTEXT_ENV]), output)
implementation.main()
