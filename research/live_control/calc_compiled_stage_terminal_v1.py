"""Translate a Calc stage receipt into a fail-closed compiled-core terminal.

This bridge does not execute input, revalidate a target, or score task effects.
"""
import copy

from research.live_control.calc_compiled_receipt_v1 import map_receipt


def to_core_terminal(receipt):
    projection = map_receipt(receipt)
    # A stage receipt by itself does not prove a fresh action/effect association.
    # Even a completed stage needs a separate admission and effect binding before
    # it can be promoted to a completed core action.
    terminal = {'status': 'delivery_uncertain', 'action_id': None,
                'effect_ref': None,
                'release': {'verified': projection['release'] == 'verified_empty',
                            'keys_down': [], 'buttons_down': []}}
    return terminal, projection

def make_stage_executor(run_stage, retain_receipt):
    """Build an executor that retains the returned stage before handing off."""
    if not callable(run_stage) or not callable(retain_receipt):
        raise ValueError('stage runner and receipt sink must be callable')

    def execute(payload):
        receipt = run_stage(copy.deepcopy(payload))
        terminal, projection = to_core_terminal(receipt)
        retain_receipt(copy.deepcopy({'receipt': receipt, 'projection': projection}))
        return terminal

    return execute
