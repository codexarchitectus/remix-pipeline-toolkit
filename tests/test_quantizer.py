"""Tests for src/pipeline/quantizer.py."""

import pytest
import pretty_midi
import numpy as np

from src.pipeline.quantizer import quantize_midi, assign_gm_programs, process_midi_files
from src.config import STEM_MIDI_PROGRAMS


def make_pretty_midi_with_notes(note_times: list[tuple[float, float, int]]) -> pretty_midi.PrettyMIDI:
    """Build a PrettyMIDI object with notes at specified (start, end, pitch) times."""
    pm = pretty_midi.PrettyMIDI(initial_tempo=120)
    instr = pretty_midi.Instrument(program=0, name="Test")
    for start, end, pitch in note_times:
        instr.notes.append(pretty_midi.Note(velocity=80, pitch=pitch, start=start, end=end))
    pm.instruments.append(instr)
    return pm


class TestQuantizeMidi:
    def test_notes_snap_to_grid(self):
        bpm = 120.0
        # At 120 BPM, beat = 0.5s, 1/16 = 0.125s
        # Note starting at 0.06 should snap to 0.0, note at 0.19 should snap to 0.25 (2nd 1/16)
        pm = make_pretty_midi_with_notes([
            (0.06, 0.20, 60),
            (0.19, 0.35, 62),
        ])
        result = quantize_midi(pm, bpm=bpm, resolution=16)
        starts = [n.start for instr in result.instruments for n in instr.notes]
        # All starts should be multiples of 0.125
        grid = 0.125
        for s in starts:
            assert abs(s % grid) < 1e-6 or abs(s % grid - grid) < 1e-6, \
                f"Note at {s} not on 1/16 grid (grid={grid})"

    def test_zero_length_notes_get_minimum_length(self):
        bpm = 120.0
        pm = make_pretty_midi_with_notes([
            (0.0, 0.001, 60),  # very short note
        ])
        result = quantize_midi(pm, bpm=bpm, resolution=16)
        for instr in result.instruments:
            for note in instr.notes:
                assert note.end > note.start, "Note end must be after start"

    def test_quantize_preserves_note_count(self):
        pm = make_pretty_midi_with_notes([(i * 0.13, i * 0.13 + 0.1, 60 + i) for i in range(8)])
        original_count = sum(len(i.notes) for i in pm.instruments)
        result = quantize_midi(pm, bpm=120.0, resolution=16)
        quantized_count = sum(len(i.notes) for i in result.instruments)
        assert quantized_count == original_count


class TestAssignGmPrograms:
    def test_drums_gets_drum_flag(self):
        pm = make_pretty_midi_with_notes([(0.0, 0.5, 38)])
        assign_gm_programs(pm, "drums")
        for instr in pm.instruments:
            assert instr.is_drum is True

    def test_bass_gets_correct_program(self):
        pm = make_pretty_midi_with_notes([(0.0, 0.5, 40)])
        assign_gm_programs(pm, "bass")
        expected_program = STEM_MIDI_PROGRAMS["bass"]["program"]
        for instr in pm.instruments:
            assert instr.program == expected_program

    def test_vocals_program(self):
        pm = make_pretty_midi_with_notes([(0.0, 0.5, 60)])
        assign_gm_programs(pm, "vocals")
        expected = STEM_MIDI_PROGRAMS["vocals"]["program"]
        assert pm.instruments[0].program == expected

    def test_unknown_stem_does_not_crash(self):
        pm = make_pretty_midi_with_notes([(0.0, 0.5, 60)])
        assign_gm_programs(pm, "unknown_stem_xyz")
        # Should be a no-op
        assert len(pm.instruments) == 1

    def test_creates_instrument_when_empty(self):
        pm = pretty_midi.PrettyMIDI(initial_tempo=120)
        assert len(pm.instruments) == 0
        assign_gm_programs(pm, "piano")
        assert len(pm.instruments) == 1
        assert pm.instruments[0].program == STEM_MIDI_PROGRAMS["piano"]["program"]
