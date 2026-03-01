"""Combine all analysis modules into a unified musical blueprint."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from src.config import log, success, header
from src.analysis.bpm import detect_bpm, tempo_feel
from src.analysis.key_detection import detect_key, compatible_keys
from src.analysis.chord_detection import detect_chords
from src.analysis.structure import detect_structure
from src.analysis.energy import (
    analyze_energy,
    analyze_frequency_balance,
    describe_energy_arc,
)


def generate_blueprint(
    audio_path: str | Path,
    output_path: str | Path | None = None,
    visualize: bool = False,
) -> dict:
    """Full analysis of a reference track → musical blueprint JSON.

    Args:
        audio_path: Path to audio file.
        output_path: Where to write blueprint JSON. Defaults to <audio>.blueprint.json.
        visualize: Print ASCII energy/structure charts.

    Returns:
        Blueprint dict.
    """
    import librosa

    audio_path = Path(audio_path)
    header(f"ANALYZING: {audio_path.name}")

    log("Loading audio...")
    y, sr = librosa.load(str(audio_path), sr=44100)
    duration = librosa.get_duration(y=y, sr=sr)
    success(f"Duration: {duration:.1f}s ({duration / 60:.1f} min)")

    # BPM
    bpm = detect_bpm(y, sr)

    # Key
    log("Detecting key...")
    key_info = detect_key(y, sr)
    success(f"Key: {key_info['full']} (Camelot {key_info['camelot']})")

    # Chords
    log("Detecting chords...")
    chords = detect_chords(y, sr, bpm=bpm)
    unique_chords = list({c["chord"] for c in chords if c["chord"] != "N"})
    success(f"Chords: {', '.join(unique_chords[:8])}")

    # Structure
    log("Detecting structure...")
    structure = detect_structure(y, sr)
    labels = [s["label"] for s in structure]
    success(f"Structure: {' → '.join(labels)}")

    # Energy
    log("Analyzing energy...")
    energy = analyze_energy(y, sr)
    success(f"Peak energy at {energy['peak_energy_time']:.1f}s")

    # Frequency balance
    log("Analyzing frequency balance...")
    freq_balance = analyze_frequency_balance(y, sr)

    # Build blueprint
    blueprint = {
        "_meta": {"source": audio_path.name, "version": "1.0"},
        "tempo": {"bpm": round(bpm, 1), "feel": tempo_feel(bpm)},
        "key": key_info,
        "chord_progression": chords,
        "unique_chords": unique_chords,
        "structure": structure,
        "structure_summary": " → ".join(labels),
        "energy_profile": energy,
        "frequency_balance": freq_balance,
        "duration_seconds": round(duration, 2),
        "remix_hints": {
            "compatible_keys": compatible_keys(key_info["key"], key_info["mode"]),
            "half_time_bpm": round(bpm / 2, 1),
            "double_time_bpm": round(bpm * 2, 1),
            "energy_arc": describe_energy_arc(energy["energy_curve"]),
        },
    }

    # Save
    if output_path is None:
        output_path = audio_path.with_suffix(".blueprint.json")
    output_path = Path(output_path)

    with open(output_path, "w") as f:
        json.dump(blueprint, f, indent=2)

    success(f"Blueprint saved: {output_path}")

    if visualize:
        _print_visualization(blueprint)

    return blueprint


def _print_visualization(bp: dict):
    """ASCII visualization of energy curve and structure."""
    curve = bp["energy_profile"]["energy_curve"]
    width = min(len(curve), 50)
    height = 8
    indices = np.linspace(0, len(curve) - 1, width).astype(int)
    resampled = [curve[i] for i in indices]

    print(f"\n  ENERGY CURVE")
    for row in range(height, 0, -1):
        threshold = row / height
        line = "  | "
        for val in resampled:
            line += "#" if val >= threshold else ("." if val >= threshold - 0.1 else " ")
        print(line + " |")
    dur = bp["duration_seconds"]
    print(f"  0s{' ' * (width - 2)}{dur:.0f}s")

    print(f"\n  STRUCTURE: {bp['structure_summary']}")
