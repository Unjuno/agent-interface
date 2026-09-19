"""Optional pure MotorState v1 runtime seam; no backend side effects."""
from .adapter import MotorStateAdapterError, motor_state_from_native_result
__all__=["MotorStateAdapterError","motor_state_from_native_result"]
