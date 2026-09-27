"""Experimental finality attestation; notifications only, never ACK or action."""
import re


def classify(joined_exit, response, seal, stream_id):
    """None means the owned producer has not joined; ownership is host-supplied."""
    if joined_exit is None:
        return 'WAIT_PRODUCER'
    if type(joined_exit) is not int:
        return 'UNKNOWN'
    if joined_exit != 0:
        return 'PRODUCER_FAILED'
    if not isinstance(response, dict):
        return 'UNKNOWN'
    if (response.get('schema') != 'agent-interface/experimental-inbox-read-v1'
            or response.get('authority') != 'none'
            or response.get('acknowledged') is not False
            or response.get('input_dispatched') is not False
            or response.get('problem') is not None):
        return 'UNKNOWN'
    if response.get('tail_state') == 'incomplete':
        return 'INCOMPLETE'
    if response.get('records') != [] or response.get('tail_state') != 'end':
        return 'UNKNOWN'
    fields = {'schema', 'stream_id', 'final_size', 'last_sequence', 'sha256'}
    if (not isinstance(seal, dict) or set(seal) != fields
            or seal['schema'] != 'experimental-final-extent-v1'
            or seal['stream_id'] != stream_id
            or type(seal['final_size']) is not int
            or not 0 <= seal['final_size'] <= 1048576
            or type(seal['last_sequence']) is not int
            or not 0 <= seal['last_sequence'] < 2**63-1
            or not isinstance(seal['sha256'], str)
            or re.fullmatch('[0-9a-f]{64}', seal['sha256']) is None):
        return 'UNKNOWN'
    cursor = response.get('next_cursor')
    if (not isinstance(cursor, dict)
            or cursor.get('schema') != 'agent-interface/experimental-read-cursor-v1'
            or cursor.get('stream_id') != stream_id
            or type(cursor.get('offset')) is not int
            or type(cursor.get('next_sequence')) is not int
            or cursor['offset'] != seal['final_size']
            or cursor['next_sequence'] != seal['last_sequence'] + 1
            or cursor.get('prefix_sha256') != seal['sha256']):
        return 'UNKNOWN'
    return 'COMPLETE'
