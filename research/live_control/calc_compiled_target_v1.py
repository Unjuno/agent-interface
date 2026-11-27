"""Bind a Calc-shaped compiled graph to the caller's final selected target."""
from research.live_control.calc_compiled_method_v1 import compile_calc_method


def make_calc_interface_factory(*, interface_id, session_scope, surface):
    """Return a graph builder; references alone never grant input authority."""
    def build(payload):
        if type(payload) is not dict or type(payload.get('target')) is not dict:
            raise ValueError('caller-selected target mapping required')
        target = payload['target']
        return compile_calc_method(interface_id=interface_id, session_scope=session_scope,
            surface=surface, sheet_handle=target.get('sheet'),
            save_handle=target.get('save'), confirm_handle=target.get('confirm'))
    return build