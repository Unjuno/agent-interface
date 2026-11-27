"""Bounded Calc-shaped method graph; evidence and authority are external."""
from runtime.core_v1.compiled_gui import validate


def compile_calc_method(*, interface_id, session_scope, surface, sheet_handle,
                        save_handle, confirm_handle):
    values = (interface_id, session_scope, surface, sheet_handle, save_handle, confirm_handle)
    if any(type(value) is not str or not value for value in values):
        raise ValueError('nonempty scope and target references required')
    if len({sheet_handle, save_handle, confirm_handle}) != 3:
        raise ValueError('distinct target references required')
    def symbol(handle, identity, dependencies):
        return {'kind': 'target_reference', 'target_reference': handle,
                'identity_predicate': identity, 'dependencies': dependencies}
    def action(target, operation, expected):
        return {'target_symbol': target, 'operation': operation, 'expected_effect': expected}
    def branch(when, outcome, action_name=None, next_state=None):
        return {'when': when, 'outcome': outcome, 'action': action_name,
                'next_state': next_state, 'reason': None}
    return validate({
        'format': 'compiled-gui-interface-v1', 'interface_id': interface_id,
        'session_scope': session_scope, 'surface': surface,
        'predicates': ['cells_match', 'sheet_target_present', 'save_target_present',
                       'dialog_present', 'dialog_absent', 'confirm_target_present', 'saved_indication'],
        'symbols': {
            'sheet': symbol(sheet_handle, 'sheet_target_present', ['sheet_target_present', 'dialog_absent']),
            'save': symbol(save_handle, 'save_target_present', ['save_target_present', 'cells_match', 'dialog_absent']),
            'confirm': symbol(confirm_handle, 'confirm_target_present',
                              ['confirm_target_present', 'dialog_present', 'cells_match']),
        },
        'actions': {
            'enter': action('sheet', 'enter_expected_cells', {'cells_match': True}),
            'save': action('save', 'open_save_dialog', {'dialog_present': True}),
            'confirm': action('confirm', 'confirm_save_format', {'saved_indication': True}),
        },
        'method': {'name': 'enter_cells_save_confirm', 'version': '1',
                   'initial_state': 'initial', 'max_transitions': 3, 'max_runtime_ms': 10000,
                   'states': {
                       'initial': {'branches': [branch({'cells_match': False,
                                                        'sheet_target_present': True,
                                                        'dialog_present': False, 'dialog_absent': True}, 'action', 'enter', 'entered')]},
                       'entered': {'branches': [branch({'cells_match': True,
                                                        'save_target_present': True,
                                                        'dialog_present': False, 'dialog_absent': True}, 'action', 'save', 'dialog')]},
                       'dialog': {'branches': [branch({'cells_match': True, 'dialog_present': True,
                                                       'confirm_target_present': True}, 'action', 'confirm', 'saved')]},
                       'saved': {'branches': [branch({'saved_indication': True,
                                                      'dialog_present': False, 'dialog_absent': True}, 'complete')]},
                   }},
    })