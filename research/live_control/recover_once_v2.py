"""Single read with an attached model-facing view; original evidence preserved."""
from recover_once_v1 import recover_once as read_once
from recovery_view_v1 import present
from unix_json_deadline import exchange


def recover_once(path, timeout=3, transport=exchange):
    result = read_once(path, timeout=timeout, transport=transport)
    return dict(result, recovery=present(result))
