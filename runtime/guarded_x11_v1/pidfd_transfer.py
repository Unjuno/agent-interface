"""Experimental nonblocking transfer of one descriptor over a private socket.

The receiver owns a successfully returned fd. This transport does not establish
its provenance, validate it as a pidfd, provide acknowledgement, or impose an
overall deadline. Both callers retain ownership of their socket endpoints.
"""

import array
import os
import socket

_MARKER = b'P'
_MAX_RIGHTS = 8
# Linux UAPI SCM_PIDFD; Python versions may not expose this constant.
_SCM_PIDFD = getattr(socket, 'SCM_PIDFD', 4)


class TransferError(RuntimeError):
    pass


def _validate_socket(sock):
    if (sock.family != socket.AF_UNIX
            or sock.type != socket.SOCK_STREAM):
        raise ValueError('dedicated Unix stream socket required')
    if sock.getblocking():
        raise ValueError('socket must be nonblocking')


def send_pidfd(sock, fd):
    _validate_socket(sock)
    if type(fd) is not int or fd < 0:
        raise ValueError('invalid descriptor')
    sent = sock.sendmsg([_MARKER], [
        (socket.SOL_SOCKET, socket.SCM_RIGHTS, array.array('i', [fd]))])
    if sent != 1:
        raise TransferError('incomplete send')


def receive_pidfd(sock):
    _validate_socket(sock)
    size = array.array('i').itemsize
    payload, ancillary, flags, _ = sock.recvmsg(
        1, socket.CMSG_SPACE(size * _MAX_RIGHTS), socket.MSG_CMSG_CLOEXEC)
    descriptors = []
    try:
        valid = True
        for level, kind, data in ancillary:
            if level != socket.SOL_SOCKET or kind not in (socket.SCM_RIGHTS, _SCM_PIDFD):
                valid = False
                continue
            if kind != socket.SCM_RIGHTS:
                valid = False
            if len(data) % size:
                valid = False
            values = array.array('i')
            values.frombytes(data[:len(data) - len(data) % size])
            descriptors.extend(values)
        if (payload != _MARKER or flags & (socket.MSG_CTRUNC | socket.MSG_TRUNC)
                or not valid or len(descriptors) != 1):
            raise TransferError('malformed descriptor message')
        if os.get_inheritable(descriptors[0]):
            raise TransferError('received descriptor is inheritable')
        return descriptors.pop()
    finally:
        close_error = None
        for fd in descriptors:
            try:
                os.close(fd)
            except OSError as error:
                if close_error is None:
                    close_error = error
        if close_error is not None:
            raise close_error
