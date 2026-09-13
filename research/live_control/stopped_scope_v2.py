"""Recognize explicit rejected action identity; retain uncertainty for legacy events."""
from stopped_scope_v1 import validate_scope, boundary as previous_boundary

def boundary(record, events, action_id):
    if action_id is not None and record.get('event') == 'rejected':
        identity = record.get('id')
        request = record.get('transport_request_id')
        if (record.get('op') != 'submit' or type(identity) is not str or not identity
                or type(request) is not str or not request):
            return 'unattributed_rejection'
        return 'boundary' if identity == action_id else None
    return previous_boundary(record, events, action_id)
