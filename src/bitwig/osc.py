"""Minimal OSC 1.0 message builder — no external dependencies.

OSC wire format:
  - Address string: null-terminated, padded to 4-byte boundary
  - Type tag string: starts with ',', null-terminated, padded to 4-byte boundary
  - Arguments: packed big-endian
    - int   → struct '>i' (4 bytes)
    - float → struct '>f' (4 bytes)
    - str   → null-terminated, padded to 4-byte boundary
    - bool  → type tag 'T' or 'F', no data bytes
"""

import struct


def pad4(data: bytes) -> bytes:
    """Pad bytes to the next 4-byte boundary with null bytes."""
    remainder = len(data) % 4
    if remainder == 0:
        return data
    return data + b"\x00" * (4 - remainder)


def _encode_string(s: str) -> bytes:
    """Encode an OSC string: UTF-8, null-terminated, 4-byte padded."""
    return pad4(s.encode("utf-8") + b"\x00")


def build_message(address: str, *args) -> bytes:
    """Build a complete OSC message from an address and arguments.

    Supported argument types:
      - int   → 'i'
      - float → 'f'
      - str   → 's'
      - bool  → 'T' or 'F' (no data bytes)

    Args:
        address: OSC address string (e.g. '/remix/play')
        *args: Arguments to include in the message.

    Returns:
        Raw OSC message bytes ready to send via UDP.
    """
    type_tags = ","
    arg_bytes = b""

    for arg in args:
        if isinstance(arg, bool):
            type_tags += "T" if arg else "F"
            # bools have no data bytes
        elif isinstance(arg, int):
            type_tags += "i"
            arg_bytes += struct.pack(">i", arg)
        elif isinstance(arg, float):
            type_tags += "f"
            arg_bytes += struct.pack(">f", arg)
        elif isinstance(arg, str):
            type_tags += "s"
            arg_bytes += _encode_string(arg)
        else:
            raise TypeError(f"Unsupported OSC argument type: {type(arg)}")

    return _encode_string(address) + _encode_string(type_tags) + arg_bytes
