"""Tests for src/config.py — presets, constants, logging utils."""

import io
import sys

import pytest

from src.config import (
    SENSITIVITY_PRESETS,
    STEM_MIDI_PROGRAMS,
    set_quiet,
    log,
    success,
    warn,
    error,
    Color,
)


class TestSensitivityPresets:
    def test_all_presets_exist(self):
        assert set(SENSITIVITY_PRESETS.keys()) == {"low", "medium", "high"}

    def test_preset_keys(self):
        for name, preset in SENSITIVITY_PRESETS.items():
            assert "onset_threshold" in preset, f"{name} missing onset_threshold"
            assert "min_note_length" in preset, f"{name} missing min_note_length"

    def test_preset_ordering(self):
        # Higher sensitivity → lower threshold, shorter min note
        assert SENSITIVITY_PRESETS["high"]["onset_threshold"] < SENSITIVITY_PRESETS["low"]["onset_threshold"]
        assert SENSITIVITY_PRESETS["high"]["min_note_length"] < SENSITIVITY_PRESETS["low"]["min_note_length"]


class TestStemMidiPrograms:
    EXPECTED_STEMS = {"vocals", "drums", "bass", "guitar", "piano", "other"}

    def test_all_stems_present(self):
        assert set(STEM_MIDI_PROGRAMS.keys()) == self.EXPECTED_STEMS

    def test_stem_fields(self):
        for stem, info in STEM_MIDI_PROGRAMS.items():
            assert "program" in info, f"{stem} missing program"
            assert "channel" in info, f"{stem} missing channel"
            assert "name" in info, f"{stem} missing name"
            assert "is_drum" in info, f"{stem} missing is_drum"

    def test_drums_channel_9(self):
        assert STEM_MIDI_PROGRAMS["drums"]["channel"] == 9

    def test_drums_is_drum_flag(self):
        assert STEM_MIDI_PROGRAMS["drums"]["is_drum"] is True

    def test_non_drums_not_drum(self):
        for stem in ["vocals", "bass", "guitar", "piano", "other"]:
            assert STEM_MIDI_PROGRAMS[stem]["is_drum"] is False

    def test_channels_unique(self):
        channels = [info["channel"] for info in STEM_MIDI_PROGRAMS.values()]
        assert len(channels) == len(set(channels)), "Duplicate MIDI channels found"


class TestQuietMode:
    def test_quiet_suppresses_log(self, capsys):
        set_quiet(True)
        log("should be hidden")
        captured = capsys.readouterr()
        assert "should be hidden" not in captured.out
        set_quiet(False)  # reset

    def test_quiet_suppresses_success(self, capsys):
        set_quiet(True)
        success("also hidden")
        captured = capsys.readouterr()
        assert "also hidden" not in captured.out
        set_quiet(False)

    def test_error_always_prints(self, capsys):
        set_quiet(True)
        error("always visible")
        captured = capsys.readouterr()
        assert "always visible" in captured.out
        set_quiet(False)

    def test_normal_mode_log_visible(self, capsys):
        set_quiet(False)
        log("visible message")
        captured = capsys.readouterr()
        assert "visible message" in captured.out
