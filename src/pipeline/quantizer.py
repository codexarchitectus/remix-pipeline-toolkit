"""MIDI quantization and GM instrument assignment."""

from pathlib import Path

import pretty_midi

from src.config import STEM_MIDI_PROGRAMS, QUANTIZE_RESOLUTION, log, success, warn


def process_midi_files(
    midi_files: list[Path],
    bpm: float = 120.0,
    quantize: bool = True,
    resolution: int = QUANTIZE_RESOLUTION,
) -> None:
    """Assign GM programs and optionally quantize a list of MIDI files (in place).

    Args:
        midi_files: Paths to MIDI files to process.
        bpm: Tempo used for quantization grid.
        quantize: Whether to snap notes to the grid.
        resolution: Quantization grid (e.g. 16 = 1/16th notes).
    """
    for midi_path in midi_files:
        try:
            pm = pretty_midi.PrettyMIDI(str(midi_path))
            stem_name = midi_path.stem.lower()

            assign_gm_programs(pm, stem_name)

            if quantize:
                pm = quantize_midi(pm, bpm, resolution)

            pm.write(str(midi_path))
            log(f"  Processed: {midi_path.name}")

        except Exception as e:
            warn(f"  Could not process {midi_path.name}: {e}")


def assign_gm_programs(pm: pretty_midi.PrettyMIDI, stem_name: str) -> None:
    """Assign GM program numbers and MIDI channels based on stem name.

    Modifies the PrettyMIDI object's instruments in place.
    """
    # Match stem name to our config (fuzzy — handle "vocals.mid", "bass.wav", etc.)
    matched = None
    for key in STEM_MIDI_PROGRAMS:
        if key in stem_name:
            matched = key
            break

    if matched is None:
        return

    info = STEM_MIDI_PROGRAMS[matched]

    if not pm.instruments:
        # Create an instrument if none exists
        instr = pretty_midi.Instrument(
            program=info["program"],
            is_drum=info.get("is_drum", False),
            name=info["name"],
        )
        pm.instruments.append(instr)
        return

    for instr in pm.instruments:
        instr.program = info["program"]
        instr.is_drum = info.get("is_drum", False)
        instr.name = info["name"]
        # Set channel by rebuilding notes with correct channel
        # pretty_midi handles channel routing via is_drum flag and program


def quantize_midi(
    pm: pretty_midi.PrettyMIDI,
    bpm: float,
    resolution: int = 16,
) -> pretty_midi.PrettyMIDI:
    """Snap all note start/end times to the nearest grid position.

    Args:
        pm: PrettyMIDI object to quantize.
        bpm: Tempo for computing grid spacing.
        resolution: Number of subdivisions per beat (16 = 1/16th notes).

    Returns:
        New PrettyMIDI object with quantized timings.
    """
    beat_duration = 60.0 / bpm
    grid_size = beat_duration / (resolution / 4)  # 1/16 of a beat at resolution=16

    def snap(t: float) -> float:
        return round(t / grid_size) * grid_size

    for instr in pm.instruments:
        for note in instr.notes:
            start_snapped = snap(note.start)
            end_snapped = snap(note.end)
            # Ensure minimum note length (at least one grid cell)
            if end_snapped <= start_snapped:
                end_snapped = start_snapped + grid_size
            note.start = start_snapped
            note.end = end_snapped

    return pm
