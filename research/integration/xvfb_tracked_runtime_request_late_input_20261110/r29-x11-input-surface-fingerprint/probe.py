#!/usr/bin/env python3
"""Read-only X11 setup fingerprint comparison across transport aliases."""
import hashlib
import json
import os
from pathlib import Path
import time

from Xlib import display


NAMES = {
    'unix_direct_same_server': ':88',
    'tcp_direct_same_server': '127.0.0.1:88',
    'tcp_proxy_alias_same_server': '127.0.0.1:89',
    'unix_direct_distinct_server': ':90',
}


def serial(value):
    if isinstance(value, bytes):
        return value.decode('utf-8', errors='replace')
    return value


def inspect_connection(name, display_name):
    conn = display.Display(display_name)
    proto = conn.display
    setup = proto.info
    socket_obj = proto.socket
    roots = []
    for screen in setup.roots:
        roots.append({
            'root_window_id': int(screen.root),
            'width_px': int(screen.width_in_pixels),
            'height_px': int(screen.height_in_pixels),
            'root_visual': int(screen.root_visual),
            'root_depth': int(screen.root_depth),
        })
    stable = {
        'vendor': serial(setup.vendor),
        'release_number': int(setup.release_number),
        'protocol_major_version': int(setup.protocol_major_version),
        'protocol_minor_version': int(setup.protocol_minor_version),
        'roots': roots,
    }
    fingerprint = hashlib.sha256(json.dumps(
        stable, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    row = {
        'display_name': display_name,
        'transport_local_address': serial(socket_obj.getsockname()),
        'transport_peer_address': serial(socket_obj.getpeername()),
        'client_resource_id_base': int(setup.resource_id_base),
        'client_resource_id_mask': int(setup.resource_id_mask),
        'server_setup_candidate': stable,
        'server_setup_candidate_sha256': fingerprint,
        'x_resource_extension_present': bool(
            conn.has_extension('X-Resource')),
    }
    return conn, row


def process_identity(display_number):
    lock_path = Path(f'/tmp/.X{display_number}-lock')
    socket_path = Path(f'/tmp/.X11-unix/X{display_number}')
    row = {'display_number': display_number,
           'lock_file': str(lock_path), 'socket_file': str(socket_path)}
    try:
        pid = int(lock_path.read_text(encoding='ascii').strip())
        stat_text = Path(f'/proc/{pid}/stat').read_text(encoding='ascii')
        # Linux proc stat's comm field can contain spaces and parentheses.
        tail = stat_text[stat_text.rfind(')') + 2:].split()
        row.update(server_pid=pid, server_start_ticks=int(tail[19]),
                   server_cmdline=Path(f'/proc/{pid}/cmdline').read_bytes()
                       .replace(b'\0', b' ').decode(errors='replace').strip())
    except (OSError, ValueError, IndexError) as error:
        row['host_process_identity_error'] = type(error).__name__
    try:
        info = socket_path.stat()
        row['unix_socket_device'] = int(info.st_dev)
        row['unix_socket_inode'] = int(info.st_ino)
    except OSError as error:
        row['unix_socket_stat_error'] = type(error).__name__
    return row


def main():
    connections = {}
    observations = {}
    try:
        for label, display_name in NAMES.items():
            conn, row = inspect_connection(label, display_name)
            connections[label] = conn
            observations[label] = row
        same_direct = (observations['unix_direct_same_server']
                       ['server_setup_candidate_sha256']
                       == observations['tcp_direct_same_server']
                       ['server_setup_candidate_sha256'])
        same_proxy = (observations['unix_direct_same_server']
                      ['server_setup_candidate_sha256']
                      == observations['tcp_proxy_alias_same_server']
                      ['server_setup_candidate_sha256'])
        different_equal = (observations['unix_direct_same_server']
                           ['server_setup_candidate_sha256']
                           == observations['unix_direct_distinct_server']
                           ['server_setup_candidate_sha256'])
        result = {
            'schema': 'agent-interface/x11-input-surface-fingerprint-r29-v1',
            'observed_monotonic_ns': time.monotonic_ns(),
            'scope': 'local Xvfb only; read-only setup metadata, no input',
            'connections': observations,
            'host_process_identity': [process_identity(88), process_identity(90)],
            'comparisons': {
                'unix_vs_direct_tcp_same_server_candidate_equal': same_direct,
                'unix_vs_tcp_proxy_alias_same_server_candidate_equal': same_proxy,
                'candidate_equal_across_distinct_xvfb_servers': different_equal,
                'interpretation': (
                    'Candidate equal across two distinct Xvfb processes is '
                    'not a unique server identity; candidate inequality across '
                    'the same server aliases means it is not alias-stable.'),
            },
        }
        print(json.dumps(result, sort_keys=True, indent=2))
    finally:
        for conn in connections.values():
            conn.close()


if __name__ == '__main__':
    main()
