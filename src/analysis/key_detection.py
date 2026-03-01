"""Key and scale detection using the Krumhansl-Schmuckler algorithm."""

import numpy as np

# Krumhansl-Schmuckler key profiles (major and minor)
_KS_MAJOR = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
_KS_MINOR = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])

_NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# Camelot wheel mapping: (note_index, mode) -> camelot code
_CAMELOT = {
    # Major keys (B suffix)
    (0,  "major"): "8B",  # C
    (1,  "major"): "3B",  # C#/Db
    (2,  "major"): "10B", # D
    (3,  "major"): "5B",  # D#/Eb
    (4,  "major"): "12B", # E
    (5,  "major"): "7B",  # F
    (6,  "major"): "2B",  # F#/Gb
    (7,  "major"): "9B",  # G
    (8,  "major"): "4B",  # G#/Ab
    (9,  "major"): "11B", # A
    (10, "major"): "6B",  # A#/Bb
    (11, "major"): "1B",  # B
    # Minor keys (A suffix)
    (0,  "minor"): "5A",  # Cm
    (1,  "minor"): "12A", # C#m
    (2,  "minor"): "7A",  # Dm
    (3,  "minor"): "2A",  # D#m/Ebm
    (4,  "minor"): "9A",  # Em
    (5,  "minor"): "4A",  # Fm
    (6,  "minor"): "11A", # F#m
    (7,  "minor"): "6A",  # Gm
    (8,  "minor"): "1A",  # G#m/Abm
    (9,  "minor"): "8A",  # Am
    (10, "minor"): "3A",  # A#m/Bbm
    (11, "minor"): "10A", # Bm
}


def detect_key(y: np.ndarray, sr: int) -> dict:
    """Detect musical key using Krumhansl-Schmuckler algorithm.

    Returns:
        dict with keys: key, mode, full, confidence, camelot
    """
    import librosa

    chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
    mean_chroma = chroma.mean(axis=1)  # 12-element pitch class profile

    best_score = -np.inf
    best_key = 0
    best_mode = "major"

    for i in range(12):
        rotated = np.roll(mean_chroma, -i)
        major_score = np.corrcoef(rotated, _KS_MAJOR)[0, 1]
        minor_score = np.corrcoef(rotated, _KS_MINOR)[0, 1]

        if major_score > best_score:
            best_score = major_score
            best_key = i
            best_mode = "major"

        if minor_score > best_score:
            best_score = minor_score
            best_key = i
            best_mode = "minor"

    # Confidence: how much better the winner is vs runner-up
    # Simplified: use the correlation coefficient directly (range -1..1 → 0..1)
    confidence = round((best_score + 1) / 2, 3)

    key_name = _NOTE_NAMES[best_key]
    camelot = _CAMELOT.get((best_key, best_mode), "?")

    return {
        "key": key_name,
        "mode": best_mode,
        "full": f"{key_name} {best_mode}",
        "confidence": confidence,
        "camelot": camelot,
    }


def compatible_keys(key: str, mode: str) -> list[str]:
    """Return harmonically compatible keys using the Camelot wheel.

    Includes: original, relative major/minor, parallel, and ±1 neighbors.
    """
    note_idx = _NOTE_NAMES.index(key) if key in _NOTE_NAMES else 0
    camelot = _CAMELOT.get((note_idx, mode), "")

    # Build reverse lookup
    rev = {v: k for k, v in _CAMELOT.items()}

    compatible = [f"{key} {mode} (original)"]

    if not camelot:
        return compatible

    num = int(camelot[:-1])
    suffix = camelot[-1]

    # ±1 on wheel (same mode)
    for delta in [-1, 1]:
        neighbor_num = ((num - 1 + delta) % 12) + 1
        neighbor_code = f"{neighbor_num}{suffix}"
        if neighbor_code in rev:
            ni, nm = rev[neighbor_code]
            compatible.append(f"{_NOTE_NAMES[ni]} {nm}")

    # Parallel (same number, opposite suffix)
    parallel_suffix = "A" if suffix == "B" else "B"
    parallel_code = f"{num}{parallel_suffix}"
    if parallel_code in rev:
        ni, nm = rev[parallel_code]
        compatible.append(f"{_NOTE_NAMES[ni]} {nm}")

    # Relative (same Camelot number − already covered by parallel, but add explicit label)
    # Add relative major/minor by name
    if mode == "minor":
        relative_idx = (note_idx + 3) % 12
        compatible.append(f"{_NOTE_NAMES[relative_idx]} major")
    else:
        relative_idx = (note_idx - 3) % 12
        compatible.append(f"{_NOTE_NAMES[relative_idx]} minor")

    return compatible
