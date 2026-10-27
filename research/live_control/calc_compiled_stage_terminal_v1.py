"""Translate a Calc stage receipt into a fail-closed compiled-core terminal.

This bridge does not execute input, revalidate a target, or score task effects.
"""
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