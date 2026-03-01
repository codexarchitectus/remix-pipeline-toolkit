"""Audio → MIDI transcription via Basic Pitch."""

from __future__ import annotations

from pathlib import Path

from src.config import SENSITIVITY_PRESETS, log, success, error, warn


def transcribe_stems(
    stems_dir: str | Path,
    midi_dir: str | Path,
    sensitivity: str = "medium",
) -> list[Path]:
    """Transcribe all audio stems in a directory to MIDI files.

    Args:
        stems_dir: Directory containing stem audio files.
        midi_dir: Output directory for MIDI files.
        sensitivity: Preset name ("low", "medium", "high").

    Returns:
        List of paths to created MIDI files.
    """
    try:
        from basic_pitch.inference import predict
        from basic_pitch import ICASSP_2022_MODEL_PATH
    except ImportError:
        error("basic-pitch not installed. Run: pip install basic-pitch")
        return []

    stems_dir = Path(stems_dir)
    midi_dir = Path(midi_dir)
    midi_dir.mkdir(parents=True, exist_ok=True)

    preset = SENSITIVITY_PRESETS.get(sensitivity, SENSITIVITY_PRESETS["medium"])
    onset_threshold = preset["onset_threshold"]
    min_note_length = preset["min_note_length"] / 1000.0  # convert ms → seconds

    from src.config import AUDIO_EXTENSIONS, MIDI_MIN_FREQUENCY, MIDI_MAX_FREQUENCY

    audio_files = sorted(f for f in stems_dir.iterdir() if f.suffix.lower() in AUDIO_EXTENSIONS)

    if not audio_files:
        warn(f"No audio files found in {stems_dir}")
        return []

    midi_files = []
    for audio_file in audio_files:
        log(f"Transcribing: {audio_file.name}")
        try:
            model_output, midi_data, note_events = predict(
                audio_file,
                ICASSP_2022_MODEL_PATH,
                onset_threshold=onset_threshold,
                frame_threshold=0.3,
                minimum_note_length=min_note_length,
                minimum_frequency=MIDI_MIN_FREQUENCY,
                maximum_frequency=MIDI_MAX_FREQUENCY,
            )

            midi_path = midi_dir / f"{audio_file.stem}.mid"
            midi_data.write(str(midi_path))
            midi_files.append(midi_path)
            success(f"  {audio_file.stem}.mid")

        except Exception as e:
            error(f"  Failed to transcribe {audio_file.name}: {e}")

    return midi_files
