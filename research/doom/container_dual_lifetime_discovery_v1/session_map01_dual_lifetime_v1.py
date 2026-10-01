"""Run unchanged MAP01 v13 measurement composition with dual-lifetime Executor only."""
import hashlib, json
from pathlib import Path
import session_map01_v12 as base
from dual_lifetime_executor_v1 import Executor
base.Executor = Executor
import session_map01_v13 as v13

if __name__ == '__main__':
    v13.main()
