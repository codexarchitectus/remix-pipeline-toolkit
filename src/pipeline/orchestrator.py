"""Full pipeline orchestrator — analyze → separate → transcribe → build session."""

from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path

from src.config import (
    DEMUCS_MODEL, QUANTIZE_RESOLUTION,
    header, success, error, log,
)


def run_pipeline(
    audio_path: str | Path,
    output_dir: str | Path | None = None,
    model: str = DEMUCS_MODEL,
    sensitivity: str = "medium",
    bpm_override: float | None = None,
    quantize: bool = True,
    quantize_resolution: int = QUANTIZE_RESOLUTION,
    analyze: bool = True,
    visualize: bool = False,
    send_to_bitwig: bool = False,
    auto_play: bool = False,
) -> Path | None:
    """Run the complete remix pipeline on an audio file.

    Returns path to the output directory, or None on failure.
    """
    audio_path = Path(audio_path)
    track_name = audio_path.stem

    if output_dir is None:
        output_dir = Path("./remix_output") / track_name
    else:
        output_dir = Path(output_dir) / track_name
    output_dir.mkdir(parents=True, exist_ok=True)

    start = time.time()
    header(f"REMIX PIPELINE: {audio_path.name}")

    # ── Phase 1: Analysis ──
    bpm = bpm_override or 120.0
    blueprint = None

    if analyze:
        log("Phase 1/4 — Analyzing reference track")
        from src.analysis.blueprint import generate_blueprint

        blueprint_path = output_dir / "blueprint.json"
        blueprint = generate_blueprint(str(audio_path), str(blueprint_path), visualize=visualize)
        bpm = blueprint["tempo"]["bpm"]

    elif bpm_override is None:
        log("Phase 1/4 — Detecting BPM")
        import librosa
        from src.analysis.bpm import detect_bpm

        y, sr = librosa.load(str(audio_path), sr=44100)
        bpm = detect_bpm(y, sr)

    # ── Phase 2: Stem separation ──
    log("Phase 2/4 — Separating stems")
    from src.pipeline.separator import separate_stems

    stems_dir = separate_stems(audio_path, output_dir / "stems", model=model)
    if stems_dir is None:
        error("Stem separation failed. Aborting.")
        return None

    # ── Phase 3: MIDI conversion ──
    log("Phase 3/4 — Converting stems to MIDI")
    from src.pipeline.transcriber import transcribe_stems
    from src.pipeline.quantizer import process_midi_files

    midi_dir = output_dir / "midi"
    midi_files = transcribe_stems(stems_dir, midi_dir, sensitivity=sensitivity)
    process_midi_files(midi_files, bpm=bpm, quantize=quantize, resolution=quantize_resolution)

    # ── Phase 4: Session assembly ──
    log("Phase 4/4 — Assembling session")
    from src.pipeline.separator import list_stems

    stem_files = list_stems(stems_dir)
    session_info = {
        "track": track_name,
        "source": str(audio_path),
        "bpm": bpm,
        "key": blueprint["key"]["full"] if blueprint else None,
        "structure": blueprint["structure_summary"] if blueprint else None,
        "stems": [s.name for s in stem_files],
        "midi_files": [m.name for m in midi_files],
        "config": {"model": model, "sensitivity": sensitivity, "quantize": quantize},
        "processed_at": datetime.now().isoformat(),
    }

    with open(output_dir / "session_info.json", "w") as f:
        json.dump(session_info, f, indent=2)

    # ── Bitwig ──
    if send_to_bitwig:
        log("Sending to Bitwig Studio...")
        try:
            from src.bitwig.bridge import BitwigBridge

            bw = BitwigBridge()
            bw.create_session_from_pipeline(str(output_dir))
            if auto_play:
                time.sleep(3)
                bw.play()
            bw.close()
        except Exception as e:
            error(f"Bitwig connection issue: {e}")
            log(f"Files saved — import manually from {midi_dir}")

    elapsed = time.time() - start
    success(f"Pipeline complete in {elapsed:.0f}s — {len(midi_files)} MIDI files ready")
    success(f"Output: {output_dir}")
    return output_dir


def run_album(
    album_dir: str | Path,
    output_dir: str | Path = "./remix_output",
    **kwargs,
) -> list[Path | None]:
    """Process every audio file in a folder."""
    from src.config import AUDIO_EXTENSIONS

    album_dir = Path(album_dir)
    audio_files = sorted(f for f in album_dir.iterdir() if f.suffix.lower() in AUDIO_EXTENSIONS)

    if not audio_files:
        error(f"No audio files found in {album_dir}")
        return []

    header(f"ALBUM: {album_dir.name} ({len(audio_files)} tracks)")
    results = []
    for i, audio_file in enumerate(audio_files, 1):
        log(f"Track {i}/{len(audio_files)}: {audio_file.name}")
        result = run_pipeline(audio_file, output_dir, **kwargs)
        results.append(result)

    succeeded = sum(1 for r in results if r is not None)
    success(f"Album complete: {succeeded}/{len(audio_files)} tracks processed")
    return results
