"""Candidate backend with admission-time explicit coordinate-frame resolution."""
from framed_pointer_intent_v1 import resolve_program
from session_v25 import Backend as Previous, suite


FRAME_SCHEMA = {
    "operations": ["pointer_click_in_frame", "pointer_drag_in_frame",
                   "local_target_guard_postcondition_in_frame"],
    "coordinate_frame": ["screen_chrome", "window_content"],
    "source_geometry": "exact [x,y,width,height] binding used to author points/boxes",
    "target_geometry": "latest stable pointer binding at whole-program admission",
    "runtime_guard": "existing InputOwner rechecks focus, surface, geometry and hit target before pointer input",
}


class Backend(Previous):
    def prepare(self, steps, identifier):
        prepared, records = resolve_program(steps, self.observed_pointer)
        return prepared, records
