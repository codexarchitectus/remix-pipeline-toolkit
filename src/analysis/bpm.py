"""BPM detection and tempo classification."""

import numpy as np


def detect_bpm(y: np.ndarray, sr: int) -> float:
    """Detect BPM from audio signal using librosa beat tracking.

    Handles both scalar and array return shapes across librosa versions.
    """
    import librosa

    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    # librosa >= 0.10 may return a 1-element array
    if hasattr(tempo, "__len__"):
        bpm = float(tempo[0])
    else:
        bpm = float(tempo)

    from src.config import log, success
    success(f"BPM: {bpm:.1f}")
    return bpm


def tempo_feel(bpm: float) -> str:
    """Map a BPM value to a descriptive feel string."""
    if bpm < 60:
        return "very slow / ambient"
    elif bpm < 80:
        return "slow / ballad"
    elif bpm < 100:
        return "moderate / chill"
    elif bpm < 120:
        return "mid-tempo / groove"
    elif bpm < 140:
        return "upbeat / dance"
    elif bpm < 160:
        return "fast / energetic"
    elif bpm < 180:
        return "very fast / drum & bass"
    else:
        return "extreme / hardcore"
