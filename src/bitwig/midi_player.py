"""Real-time MIDI playback via IAC Driver for Bitwig recording.

Merges all stem MIDI files into a single event stream (preserving per-stem
channel assignments) and plays them in real-time through the macOS IAC Driver.
"""

import time
from pathlib import Path


def list_iac_ports() -> list[str]:
    """Return available IAC Driver MIDI output port names."""
    try:
        import mido
        return [p for p in mido.get_output_names() if "IAC" in p]
    except ImportError:
        return []


def merge_midi_files(midi_files: list[Path]) -> list[tuple[float, object]]:
    """Merge multiple MIDI files into a single sorted event list.

    Each file's notes are played on the channel already embedded in the file
    (set by the quantizer via STEM_MIDI_PROGRAMS).

    Returns:
        List of (absolute_time_seconds, mido_message) tuples, sorted by time.
    """
    import mido

    events = []

    for midi_path in midi_files:
        try:
            mid = mido.MidiFile(str(midi_path))
            tempo = 500000  # default: 120 BPM
            current_time = 0.0

            for msg in mid:
                # msg.time is delta time in seconds when using MidiFile iteration
                current_time += msg.time
                if msg.type == "set_tempo":
                    tempo = msg.tempo
                elif not msg.is_meta:
                    events.append((current_time, msg))
        except Exception:
            pass  # skip malformed files

    events.sort(key=lambda x: x[0])
    return events


def play_stems_to_iac(
    midi_files: list[Path],
    port_name: str = "IAC Driver Bus 1",
) -> None:
    """Play all MIDI stem files simultaneously through the IAC Driver.

    Merges all files by absolute time, then sends events with correct
    inter-event delays so Bitwig receives them in real-time.

    Args:
        midi_files: List of MIDI file paths (channels set by quantizer).
        port_name: IAC Driver output port name.
    """
    try:
        import mido
    except ImportError:
        raise ImportError(
            "mido not installed. Run: pip install 'mido[ports-rtmidi]>=1.3'"
        )

    available = mido.get_output_names()
    if port_name not in available:
        # Try a fallback match
        iac_ports = [p for p in available if "IAC" in p]
        if iac_ports:
            port_name = iac_ports[0]
        else:
            raise RuntimeError(
                f"IAC Driver port not found. Available ports: {available}\n"
                "Enable IAC Driver: Audio MIDI Setup → MIDI Studio → IAC Driver"
            )

    events = merge_midi_files(midi_files)
    if not events:
        return

    with mido.open_output(port_name) as port:
        last_time = 0.0
        for abs_time, msg in events:
            delta = abs_time - last_time
            if delta > 0:
                time.sleep(delta)
            last_time = abs_time
            try:
                port.send(msg)
            except Exception:
                pass  # skip unplayable messages (e.g. meta events that slipped through)
