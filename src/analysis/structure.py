"""Song structure segmentation using MFCC self-similarity."""

import numpy as np


def detect_structure(y: np.ndarray, sr: int) -> list[dict]:
    """Detect song structure via MFCC self-similarity matrix + agglomerative segmentation.

    Returns a list of segments with labels A/B/C/..., start/end times, and duration.
    """
    import librosa

    # MFCC features
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)

    # Recurrence matrix for self-similarity
    R = librosa.segment.recurrence_matrix(mfcc, mode="affinity", sym=True)

    # Agglomerative segmentation — find boundary frames
    bounds = librosa.segment.agglomerative(R, k=min(8, R.shape[0] // 10 + 2))
    bound_times = librosa.frames_to_time(bounds, sr=sr)

    # Add start/end
    duration = librosa.get_duration(y=y, sr=sr)
    all_times = np.concatenate([[0.0], bound_times, [duration]])
    all_times = np.unique(all_times)

    # Label segments by similarity to each other (A/B/C pattern)
    # Assign labels by clustering segment centroids
    segments = []
    label_map = {}
    label_counter = 0

    for i in range(len(all_times) - 1):
        start = float(all_times[i])
        end = float(all_times[i + 1])
        dur = end - start

        if dur < 1.0:
            continue

        # Find frame index for segment midpoint
        mid_time = (start + end) / 2
        mid_frame = librosa.time_to_frames(mid_time, sr=sr)
        mid_frame = min(mid_frame, mfcc.shape[1] - 1)
        centroid = tuple(np.round(mfcc[:, mid_frame], 1))

        # Find closest existing label or assign new one
        assigned = None
        for existing_centroid, lbl in label_map.items():
            dist = np.linalg.norm(np.array(centroid) - np.array(existing_centroid))
            if dist < 5.0:  # similarity threshold
                assigned = lbl
                break

        if assigned is None:
            assigned = chr(ord("A") + label_counter % 26)
            label_map[centroid] = assigned
            label_counter += 1

        segments.append({
            "label": assigned,
            "start_time": round(start, 2),
            "end_time": round(end, 2),
            "duration": round(dur, 2),
        })

    if not segments:
        # Fallback: single segment
        duration = librosa.get_duration(y=y, sr=sr)
        segments = [{"label": "A", "start_time": 0.0, "end_time": round(duration, 2),
                     "duration": round(duration, 2)}]

    return segments
