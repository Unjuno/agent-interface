"""Opt-in XRes/Linux process-incarnation evidence, not window incarnation."""
import hashlib
import json
from pathlib import Path


def read_linux_x11_process_identity(connection, xid):
    """Hash XID + server-reported PID + /proc start ticks.

    Requires a trusted local X server whose PID namespace matches this /proc.
    No window-property fallback. Calls are synchronous, without an I/O bound.
    Same-process resource/client reuse and changes after this read are not
    excluded by this evidence.
    """
    if type(xid) is not int or xid <= 1:
        raise RuntimeError('invalid target resource')
    if not connection.has_extension('X-Resource'):
        raise RuntimeError('X-Resource unavailable')
    version = getattr(connection, '_agent_interface_xres_version', None)
    if version is None:
        reply = connection.res_query_version()
        version = (reply.server_major, reply.server_minor)
        if any(type(value) is not int or value < 0 for value in version):
            raise RuntimeError('invalid X-Resource version')
        connection._agent_interface_xres_version = version
    if (type(version) is not tuple or len(version) != 2
            or any(type(value) is not int or value < 0 for value in version)
            or version < (1, 2)):
        raise RuntimeError('X-Resource 1.2 required')
    reply = connection.res_query_client_ids([{'client': xid, 'mask': 2}])
    try:
        matches = [item for item in reply.ids if item.spec.client == xid and item.spec.mask == 2]
        if len(matches) != 1 or len(matches[0].value) != 1:
            raise RuntimeError('ambiguous local client PID')
        pid = matches[0].value[0]
    except (AttributeError, TypeError) as error:
        raise RuntimeError('invalid local client PID response') from error
    if type(pid) is not int or pid <= 0:
        raise RuntimeError('invalid local client PID')
    stat = Path('/proc', str(pid), 'stat').read_text(encoding='ascii')
    opening, closing = stat.find('('), stat.rfind(')')
    if opening < 1 or closing <= opening or stat[:opening].strip() != str(pid):
        raise RuntimeError('process stat identity mismatch')
    fields = stat[closing + 1:].split()
    if (len(fields) <= 19 or fields[0] in ('Z', 'X', 'x')
            or not fields[19].isascii() or not fields[19].isdigit()):
        raise RuntimeError('process start identity unavailable')
    payload = {'scheme': 'xres-linux-process-v1', 'xid': xid,
               'pid': pid, 'start_ticks': int(fields[19])}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode('ascii')).hexdigest()
