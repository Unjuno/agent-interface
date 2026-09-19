"""Compatibility import shim for the retained golden IPC route.

The historical session imports tile_transport from its flat
research/live_control import root. The canonical implementation remains in
research/observation_tiles/tile_transport.py and is not copied or changed.
This shim only makes that existing module visible under the historical import
name; it grants no authority and performs no I/O on import.
"""
from research.observation_tiles.tile_transport import Decoder, Encoder, Frame, packet

__all__ = ["Decoder", "Encoder", "Frame", "packet"]
