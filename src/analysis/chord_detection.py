"""Beat-aligned chord detection via chroma + cosine similarity."""

import numpy as np


# 24 chord templates (major + minor for each of 12 notes)
# Binary pitch class templates
_NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

def _make_chord_templates() -> tuple[list[str], np.ndarray]:
    """Build 24 major/minor chord templates as pitch class vectors."""
    # Major: root, major third (+4), fifth (+7)
    # Minor: root, minor third (+3), fifth (+7)
    names = []
    templates = []

    for i, note in enumerate(_NOTE_NAMES):
        # Major
        template = np.zeros(12)
        template[i % 12] = 1
        template[(i + 4) % 12] = 1
        template[(i + 7) % 12] = 1
        names.append(note)
        templates.append(template)

        # Minor
        template = np.zeros(12)
        template[i % 12] = 1
        template[(i + 3) % 12] = 1
        template[(i + 7) % 12] = 1
        names.append(f"{note}m")
        templates.append(template)

    arr = np.array(templates)  # shape (24, 12)
    # L2-normalize each template so cosine similarity stays in [-1, 1]
    norms = np.linalg.norm(arr, axis=1, keepdims=True)
    arr = arr / norms
    return names, arr


_CHORD_NAMES, _CHORD_TEMPLATES = _make_chord_templates()
_CONFIDENCE_THRESHOLD = 0.75  # cosine similarity threshold (normalized templates)


def detect_chords(y: np.ndarray, sr: int, bpm: float = 120.0) -> list[dict]:
    """Detect chord progression aligned to beats.

    Returns a list of {chord, time} dicts. Low-confidence windows are labeled "N".
    Falls back to fixed-size windows when no beats are detected (e.g. pure tones).
    """
    import librosa

    chroma = librosa.feature.chroma_cqt(y=y, sr=sr)

    # Try beat-aligned windows first
    _, beat_frames = librosa.beat.beat_track(y=y, sr=sr)

    # Fall back to fixed hop when no beats detected (e.g. pure sine waves in tests)
    if len(beat_frames) == 0:
        hop_frames = max(1, librosa.time_to_frames(60.0 / bpm, sr=sr))
        beat_frames = np.arange(0, chroma.shape[1], hop_frames)

    beat_times = librosa.frames_to_time(beat_frames, sr=sr)
    chroma_sync = librosa.util.sync(chroma, beat_frames, aggregate=np.mean)  # (12, n_beats)

    chords = []
    for i, t in enumerate(beat_times):
        chroma_vec = chroma_sync[:, i]

        norm = np.linalg.norm(chroma_vec)
        if norm < 1e-6:
            chords.append({"chord": "N", "time": round(float(t), 3)})
            continue

        chroma_norm = chroma_vec / norm

        # Cosine similarity against all templates
        sims = _CHORD_TEMPLATES @ chroma_norm  # shape (24,)
        best_idx = int(np.argmax(sims))
        confidence = float(sims[best_idx])

        chord_name = _CHORD_NAMES[best_idx] if confidence >= _CONFIDENCE_THRESHOLD else "N"
        chords.append({"chord": chord_name, "time": round(float(t), 3)})

    return chords
