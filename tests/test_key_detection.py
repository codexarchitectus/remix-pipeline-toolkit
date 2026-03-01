"""Tests for src/analysis/key_detection.py."""

import numpy as np
import pytest

from src.analysis.key_detection import detect_key, compatible_keys, _NOTE_NAMES


def make_sine_chord(frequencies: list[float], sr: int = 44100, duration: float = 3.0) -> np.ndarray:
    """Synthesize a chord as a sum of sine waves."""
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    y = np.zeros_like(t)
    for f in frequencies:
        y += np.sin(2 * np.pi * f * t)
    return (y / np.abs(y).max()).astype(np.float32)


class TestDetectKey:
    def test_a_minor_chord_returns_key(self):
        # A minor chord: A(440), C(523), E(659)
        sr = 44100
        y = make_sine_chord([440.0, 523.25, 659.25], sr=sr)
        result = detect_key(y, sr)

        assert "key" in result
        assert "mode" in result
        assert "full" in result
        assert "confidence" in result
        assert "camelot" in result

        # A+C+E is either Am or C major — both are valid
        assert result["key"] in ["A", "C"]
        assert result["mode"] in ["minor", "major"]

    def test_confidence_is_normalized(self):
        sr = 44100
        y = make_sine_chord([440.0, 523.25, 659.25], sr=sr)
        result = detect_key(y, sr)
        assert 0.0 <= result["confidence"] <= 1.0

    def test_camelot_code_format(self):
        sr = 44100
        y = make_sine_chord([440.0, 523.25, 659.25], sr=sr)
        result = detect_key(y, sr)
        camelot = result["camelot"]
        assert len(camelot) >= 2
        assert camelot[-1] in ("A", "B")
        assert camelot[:-1].isdigit()

    def test_full_is_key_plus_mode(self):
        sr = 44100
        y = make_sine_chord([440.0, 523.25, 659.25], sr=sr)
        result = detect_key(y, sr)
        assert result["full"] == f"{result['key']} {result['mode']}"


class TestCompatibleKeys:
    def test_returns_list(self):
        result = compatible_keys("A", "minor")
        assert isinstance(result, list)
        assert len(result) >= 1

    def test_original_is_first(self):
        result = compatible_keys("C", "major")
        assert "original" in result[0].lower()

    def test_all_strings(self):
        result = compatible_keys("G", "major")
        assert all(isinstance(s, str) for s in result)

    def test_minor_includes_relative_major(self):
        # A minor → C major (relative)
        result = compatible_keys("A", "minor")
        joined = " ".join(result)
        assert "C" in joined

    def test_all_notes_work(self):
        for note in _NOTE_NAMES:
            for mode in ["major", "minor"]:
                result = compatible_keys(note, mode)
                assert len(result) >= 1, f"No compatible keys for {note} {mode}"
