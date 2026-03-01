"""Energy curve analysis and frequency balance."""

import numpy as np


def analyze_energy(y: np.ndarray, sr: int) -> dict:
    """Compute RMS energy curve, normalized to 0–1, downsampled to 64 points.

    Returns:
        dict with energy_curve (list[float]), peak_energy_time (float), average_energy (float)
    """
    import librosa

    rms = librosa.feature.rms(y=y)[0]  # shape (n_frames,)
    rms_max = rms.max()
    if rms_max > 0:
        normalized = rms / rms_max
    else:
        normalized = rms

    # Downsample to 64 points
    n_points = 64
    indices = np.linspace(0, len(normalized) - 1, n_points).astype(int)
    curve = [round(float(normalized[i]), 4) for i in indices]

    # Peak time
    peak_frame = int(np.argmax(rms))
    peak_time = librosa.frames_to_time(peak_frame, sr=sr)

    return {
        "energy_curve": curve,
        "peak_energy_time": round(float(peak_time), 2),
        "average_energy": round(float(normalized.mean()), 4),
    }


def analyze_frequency_balance(y: np.ndarray, sr: int) -> dict:
    """Compute energy in 6 frequency bands, normalized to proportions summing to 1.

    Bands: sub (20-60 Hz), bass (60-250 Hz), low_mid (250-500 Hz),
           mid (500-2kHz), high_mid (2k-6kHz), high (6k-20kHz)
    """
    import librosa

    # Short-time Fourier transform
    S = np.abs(librosa.stft(y))
    freqs = librosa.fft_frequencies(sr=sr)

    bands = {
        "sub":      (20, 60),
        "bass":     (60, 250),
        "low_mid":  (250, 500),
        "mid":      (500, 2000),
        "high_mid": (2000, 6000),
        "high":     (6000, 20000),
    }

    energies = {}
    for name, (lo, hi) in bands.items():
        mask = (freqs >= lo) & (freqs <= hi)
        if mask.any():
            energies[name] = float(S[mask].mean())
        else:
            energies[name] = 0.0

    total = sum(energies.values())
    if total > 0:
        return {k: round(v / total, 4) for k, v in energies.items()}
    return {k: 0.0 for k in energies}


def describe_energy_arc(curve: list[float]) -> str:
    """Classify the energy arc pattern from a normalized energy curve."""
    if not curve:
        return "unknown"

    n = len(curve)
    first_third = np.mean(curve[: n // 3])
    last_third = np.mean(curve[2 * n // 3 :])
    middle_third = np.mean(curve[n // 3 : 2 * n // 3])
    peak_pos = np.argmax(curve) / n

    if first_third < middle_third and last_third < middle_third:
        return "build → peak → fade (classic arc)"
    elif first_third > last_third and first_third > middle_third:
        return "high start → fade (intro energy)"
    elif last_third > first_third and last_third > middle_third:
        return "build → peak at end (late bloomer)"
    elif peak_pos < 0.25:
        return "explosive start → sustained"
    else:
        return "consistent energy throughout"
