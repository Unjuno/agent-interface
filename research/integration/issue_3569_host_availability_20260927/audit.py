import json
from pathlib import Path


def audit(snapshot):
    errors = []
    if snapshot.get('schema') != 'codex-mcp-list-snapshot-v1':
        errors.append('schema')
    if snapshot.get('command') != 'codex mcp list' or snapshot.get('exit_code') != 0:
        errors.append('source_command')
    servers = snapshot.get('servers', [])
    names = [server.get('name') for server in servers]
    if len(names) != len(set(names)):
        errors.append('duplicate_server_name')
    listed = 'agent_interface_integration' in names or 'agent-interface' in names
    if snapshot.get('agent_interface_server_listed') is not listed:
        errors.append('presence_summary_mismatch')
    if any(snapshot.get(key) != 0 for key in ('task_calls', 'model_calls', 'provider_calls')):
        errors.append('unexpected_call')
    if snapshot.get('credentials_inspected') is not False:
        errors.append('credential_scope')
    if snapshot.get('persistent_config_modified') is not False:
        errors.append('configuration_mutation')

    supported = any(
        server.get('name') in ('agent_interface_integration', 'agent-interface')
        and server.get('status') == 'enabled'
        and server.get('auth') != 'Unsupported'
        for server in servers
    )
    if errors:
        status = 'FAIL_AUDIT'
    elif not listed or not supported:
        status = 'STOP_ROUTE_UNAVAILABLE'
    else:
        # A configured server alone cannot establish same-model image delivery.
        status = 'HOLD_MODEL_VISIBILITY_UNPROVEN'
    return {'status': status, 'servers': names, 'errors': errors}


if __name__ == '__main__':
    snapshot = json.loads(Path('/in/HOST_STATE.json').read_text(encoding='utf-8'))
    print(json.dumps(audit(snapshot), sort_keys=True))
