"""Stem separation via Demucs (invoked as subprocess)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from src.config import DEMUCS_MODEL, AUDIO_EXTENSIONS, log, success, error


def separate_stems(
    audio_path: str | Path,
    output_dir: str | Path,
    model: str = DEMUCS_MODEL,
) -> Path | None:
    """Separate audio into stems using Demucs.

    Invokes Demucs as a subprocess to avoid GPU memory management issues
    with direct import.

    Returns:
        Path to the stem directory (output_dir/{model}/{track_name}/), or None on failure.
    """
    audio_path = Path(audio_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    log(f"Separating stems: {audio_path.name} (model={model})")

    cmd = [
        sys.executable, "-m", "demucs",
        "-n", model,
        "--out", str(output_dir),
        str(audio_path),
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            error(f"Demucs failed:\n{result.stderr}")
            return None
    except FileNotFoundError:
        error("Demucs not found. Install with: pip install demucs")
        return None

    # Demucs writes to: output_dir/{model}/{track_name}/
    stem_dir = output_dir / model / audio_path.stem
    if not stem_dir.exists():
        error(f"Expected stem directory not found: {stem_dir}")
        return None

    stems = list_stems(stem_dir)
    success(f"Stems: {', '.join(s.stem for s in stems)}")
    return stem_dir


def list_stems(stems_dir: str | Path) -> list[Path]:
    """List audio stem files in a directory."""
    stems_dir = Path(stems_dir)
    stems = sorted(
        f for f in stems_dir.iterdir()
        if f.suffix.lower() in AUDIO_EXTENSIONS
    )
    return stems
