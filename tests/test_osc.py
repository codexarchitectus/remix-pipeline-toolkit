"""Tests for src/bitwig/osc.py — OSC 1.0 message encoding."""

import struct
import pytest

from src.bitwig.osc import build_message, pad4


class TestPad4:
    def test_already_aligned(self):
        data = b"abcd"  # 4 bytes — no padding needed
        assert pad4(data) == b"abcd"

    def test_one_byte_needs_three_padding(self):
        data = b"a"
        result = pad4(data)
        assert result == b"a\x00\x00\x00"
        assert len(result) % 4 == 0

    def test_two_bytes_needs_two_padding(self):
        data = b"ab"
        result = pad4(data)
        assert result == b"ab\x00\x00"
        assert len(result) % 4 == 0

    def test_three_bytes_needs_one_padding(self):
        data = b"abc"
        result = pad4(data)
        assert result == b"abc\x00"
        assert len(result) % 4 == 0

    def test_eight_bytes_no_padding(self):
        data = b"abcdefgh"
        assert pad4(data) == data

    def test_empty_bytes(self):
        assert pad4(b"") == b""


class TestBuildMessage:
    def test_address_only(self):
        msg = build_message("/test")
        # Address "/test\0" = 6 bytes → padded to 8
        # Type tag ",\0" = 2 bytes → padded to 4
        assert msg.startswith(b"/test\x00\x00\x00")
        assert b",\x00\x00\x00" in msg

    def test_int_argument(self):
        msg = build_message("/test", 42)
        # Should contain type tag 'i' and big-endian 42
        assert b",i\x00\x00" in msg
        assert struct.pack(">i", 42) in msg

    def test_float_argument(self):
        msg = build_message("/test", 3.14)
        assert b",f\x00\x00" in msg
        assert struct.pack(">f", 3.14) in msg

    def test_string_argument(self):
        msg = build_message("/test", "hi")
        assert b",s\x00\x00" in msg
        assert b"hi\x00\x00" in msg  # null-terminated + padded

    def test_bool_true(self):
        msg = build_message("/test", True)
        assert b",T\x00\x00" in msg

    def test_bool_false(self):
        msg = build_message("/test", False)
        assert b",F\x00\x00" in msg

    def test_bool_no_data_bytes(self):
        # Bool args don't add data bytes — message should be shorter than with an int
        msg_bool = build_message("/test", True)
        msg_int  = build_message("/test", 1)
        assert len(msg_bool) < len(msg_int)

    def test_mixed_arguments(self):
        msg = build_message("/remix/volume", "bass", 0.8)
        assert b",sf" in msg
        assert b"bass" in msg
        assert struct.pack(">f", 0.8) in msg

    def test_known_encoding(self):
        # Verify exact byte sequence for a known simple message
        # /test\0\0\0 (8 bytes) + ,i\0\0 (4 bytes) + \x00\x00\x00\x01 (4 bytes) = 16 bytes
        msg = build_message("/test", 1)
        expected = (
            b"/test\x00\x00\x00"   # address
            b",i\x00\x00"          # type tag
            b"\x00\x00\x00\x01"    # int 1
        )
        assert msg == expected

    def test_all_parts_4byte_aligned(self):
        msg = build_message("/remix/bpm", 128.0)
        assert len(msg) % 4 == 0

    def test_unsupported_type_raises(self):
        with pytest.raises(TypeError):
            build_message("/test", [1, 2, 3])
