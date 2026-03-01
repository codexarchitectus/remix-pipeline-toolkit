"""Tests for src/analysis/chord_detection.py."""

import numpy as np
import pytest

from src.analysis.chord_detection import detect_chords, _CHORD_NAMES


def make_chord_audio(frequencies: list[float], sr: int = 44100, duration: float = 4.0) -> np.ndarray:
    """Synthesize a sustained chord."""
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    y = np.zeros_like(t)
    for f in frequencies:
        y += np.sin(2 * np.pi * f * t)
    return (y / np.abs(y).max()).astype(np.float32)


class TestDetectChords:
    def test_returns_list_of_dicts(self):
        sr = 44100
        y = make_chord_audio([261.63, 329.63, 392.00], sr=sr)  # C major
        result = detect_chords(y, sr, bpm=120.0)
        assert isinstance(result, list)
        assert len(result) > 0
        for item in result:
            assert "chord" in item
            assert "time" in item

    def test_chord_values_are_valid_names_or_N(self):
        sr = 44100
        y = make_chord_audio([261.63, 329.63, 392.00], sr=sr)
        result = detect_chords(y, sr, bpm=120.0)
        valid = set(_CHORD_NAMES) | {"N"}
        for item in result:
            assert item["chord"] in valid, f"Invalid chord: {item['chord']}"

    def test_times_are_non_negative(self):
        sr = 44100
        y = make_chord_audio([261.63, 329.63, 392.00], sr=sr)
        result = detect_chords(y, sr, bpm=120.0)
        for item in result:
            assert item["time"] >= 0.0

    def test_times_are_sorted(self):
        sr = 44100
        y = make_chord_audio([261.63, 329.63, 392.00], sr=sr)
        result = detect_chords(y, sr, bpm=120.0)
        times = [item["time"] for item in result]
        assert times == sorted(times)

    def test_c_major_detected(self):
        # C+E+G strongly suggests C major
        sr = 44100
        y = make_chord_audio([261.63, 329.63, 392.00], sr=sr, duration=8.0)
        result = detect_chords(y, sr, bpm=60.0)
        chord_names = [r["chord"] for r in result if r["chord"] != "N"]
        # At least one beat should detect C
        assert any("C" in c for c in chord_names), f"Expected C in {chord_names[:10]}"
