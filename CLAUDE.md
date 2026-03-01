# Remix Pipeline Toolkit

## Project Overview

A Python CLI toolkit that automates the tedious parts of creating remixes. Given a reference audio track (mp3/wav/flac), the system:

1. **Analyzes** the track's musical DNA (key, chords, structure, energy curve, BPM)
2. **Separates** it into stems (vocals, drums, bass, guitar, piano, other) using ML
3. **Converts** each stem to MIDI
4. **Builds a Bitwig Studio session** automatically via Controller API + OSC bridge

The goal is a hobby remix workflow: drop a track in → get a blueprint + stems + MIDI → use that as scaffolding to create something new in Bitwig.

## Architecture

```
remix-toolkit/
├── CLAUDE.md                          ← You are here
├── pyproject.toml                     ← Project config, dependencies, CLI entry points
├── setup.sh                           ← One-command install script
├── src/
│   ├── __init__.py
│   ├── cli.py                         ← Main CLI (click-based). Entry points:
│   │                                     `remix run`, `remix analyze`, `remix stems`,
│   │                                     `remix midi`, `remix watch`, `remix bitwig send`
│   ├── config.py                      ← Shared config, constants, defaults
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── separator.py               ← Stem separation (wraps Demucs)
│   │   ├── transcriber.py             ← Audio→MIDI (wraps Basic Pitch)
│   │   ├── quantizer.py               ← MIDI quantization + GM instrument tagging
│   │   └── orchestrator.py            ← Full pipeline coordinator (run all phases)
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── key_detection.py           ← Key/scale detection (Krumhansl-Schmuckler)
│   │   ├── chord_detection.py         ← Chord progression extraction
│   │   ├── structure.py               ← Song structure segmentation (verse/chorus/etc)
│   │   ├── energy.py                  ← Energy/intensity curve analysis
│   │   ├── bpm.py                     ← BPM + time signature detection
│   │   └── blueprint.py               ← Combines all analysis → blueprint.json
│   └── bitwig/
│       ├── __init__.py
│       ├── bridge.py                  ← Python→Bitwig OSC bridge
│       ├── osc.py                     ← Minimal OSC message builder (no deps)
│       └── RemixPipeline.control.js   ← Bitwig Controller Extension (JS)
├── tests/
│   ├── test_config.py
│   ├── test_key_detection.py
│   ├── test_chord_detection.py
│   ├── test_quantizer.py
│   ├── test_osc.py
│   └── test_pipeline_integration.py   ← End-to-end with fixture audio
├── scripts/
│   └── install_bitwig_controller.sh   ← Copies controller JS to Bitwig's folder
└── docs/
    ├── RECIPES.md                     ← Pre-configured workflow presets
    └── BITWIG_SETUP.md                ← Bitwig integration guide
```

## Tech Stack & Dependencies

### Core (required)
- **Python 3.10+**
- **demucs** — Meta's ML stem separation (htdemucs_6s model for 6 stems)
- **basic-pitch** — Spotify's audio-to-MIDI neural net
- **pretty_midi** — MIDI file manipulation (read/write/edit)
- **librosa** — Audio analysis (BPM, chroma, beat tracking, structure)
- **numpy** — Numerical operations
- **soundfile** — Audio I/O
- **click** — CLI framework

### Optional
- **madmom** — Better beat/chord detection (if available, fall back to librosa)

### Dev
- **pytest** — Testing
- **ruff** — Linting

## Key Design Decisions

1. **Modular pipeline** — Each phase (analyze, separate, transcribe, quantize) is independent. Users can run just `remix analyze` or just `remix stems` without the full pipeline.

2. **Config cascade** — Defaults in `config.py` → overridden by CLI flags → overridden by `remix.toml` project file if present.

3. **No external OSC library** — The OSC bridge uses a minimal hand-rolled builder (`src/bitwig/osc.py`) to avoid pulling in python-osc just for sending a few UDP packets.

4. **Sensitivity presets** — Instead of exposing raw thresholds, users pick `--sensitivity low/medium/high` which maps to tuned onset_threshold + min_note_length combos.

5. **Blueprint JSON** — The analysis output is a structured JSON "blueprint" that captures musical characteristics without containing actual musical content. This is the template for building something new.

6. **Bitwig dual-path integration**:
   - **File-based** (primary): Python writes MIDI + manifest.json → Bitwig controller script watches a known directory and auto-imports
   - **OSC** (secondary): Real-time control (play/stop/mute/solo/volume/bpm) from Python

7. **GM instrument tagging** — MIDI files are tagged with General MIDI program numbers so Bitwig (or any DAW) assigns reasonable default instruments when importing.

## CLI Design

All commands use Click and live in `src/cli.py`:

```bash
# Full pipeline
remix run song.mp3 [-o output/] [--model htdemucs_6s] [--sensitivity medium] [--to-bitwig] [--play]

# Individual phases  
remix analyze song.mp3 [-o blueprint.json] [--visualize]
remix stems song.mp3 [-o stems/] [--model htdemucs_6s]
remix midi stems/ [-o midi/] [--bpm 128] [--sensitivity medium] [--no-quantize]

# Bitwig
remix bitwig send ./output/SongName/ [--play]
remix bitwig install                   # Install controller script

# Utilities
remix watch ~/Dropbox/ ~/Remixes/ [--model htdemucs_6s] [--sensitivity medium]
remix recipes [--list] [RECIPE] song.mp3
```

Entry point in pyproject.toml: `[project.scripts] remix = "src.cli:cli"`

## Configuration Defaults (src/config.py)

```python
DEMUCS_MODEL = "htdemucs_6s"        # 6 stems
MIDI_ONSET_THRESHOLD = 0.5          # medium sensitivity
MIDI_MIN_NOTE_LENGTH = 58           # ms
MIDI_MIN_FREQUENCY = 32             # Hz
MIDI_MAX_FREQUENCY = 4200           # Hz
QUANTIZE_RESOLUTION = 16            # 1/16th notes
AUDIO_EXTENSIONS = {".mp3", ".wav", ".flac", ".aiff", ".aif", ".m4a", ".ogg"}

SENSITIVITY_PRESETS = {
    "low":    {"onset_threshold": 0.7, "min_note_length": 80},
    "medium": {"onset_threshold": 0.5, "min_note_length": 58},
    "high":   {"onset_threshold": 0.3, "min_note_length": 40},
}

STEM_MIDI_PROGRAMS = {
    "vocals":  {"program": 54, "channel": 0,  "name": "Synth Voice"},
    "drums":   {"program": 0,  "channel": 9,  "name": "Standard Drums", "is_drum": True},
    "bass":    {"program": 33, "channel": 1,  "name": "Electric Bass"},
    "guitar":  {"program": 25, "channel": 2,  "name": "Acoustic Guitar"},
    "piano":   {"program": 0,  "channel": 3,  "name": "Grand Piano"},
    "other":   {"program": 48, "channel": 4,  "name": "String Ensemble"},
}

BITWIG_OSC_HOST = "127.0.0.1"
BITWIG_OSC_PORT = 8000
```

## Blueprint JSON Schema

The output of `remix analyze` looks like:

```json
{
  "_meta": { "source": "song.mp3", "version": "1.0" },
  "tempo": { "bpm": 128.0, "feel": "upbeat / dance" },
  "key": {
    "key": "A", "mode": "minor", "full": "A minor",
    "confidence": 0.87, "camelot": "8A"
  },
  "chord_progression": [
    { "chord": "Am", "time": 0.0 },
    { "chord": "F", "time": 2.4 },
    { "chord": "C", "time": 4.8 }
  ],
  "structure": [
    { "label": "A", "start_time": 0.0, "end_time": 16.2, "duration": 16.2 },
    { "label": "B", "start_time": 16.2, "end_time": 48.5, "duration": 32.3 }
  ],
  "energy_profile": {
    "energy_curve": [0.12, 0.15, ...],  // 64 points, normalized 0-1
    "peak_energy_time": 165.3,
    "average_energy": 0.54
  },
  "frequency_balance": {
    "sub": 0.08, "bass": 0.22, "low_mid": 0.18,
    "mid": 0.28, "high_mid": 0.15, "high": 0.09
  },
  "remix_hints": {
    "compatible_keys": ["A minor (original)", "C major", "A major", "D minor"],
    "half_time_bpm": 64.0,
    "double_time_bpm": 256.0,
    "energy_arc": "build → peak → fade (classic arc)"
  }
}
```

## Testing Strategy

- **Unit tests** for analysis modules (key detection, chord detection, quantizer) using known inputs
- **Integration test** using a short public-domain audio fixture (generate a test sine wave + drum pattern programmatically in the test)
- **OSC tests** verify message encoding against known byte sequences
- Run with: `pytest tests/ -v`

## Build & Run Commands

```bash
# Setup
./setup.sh                    # Creates venv, installs deps
source .venv/bin/activate

# Or manual
pip install -e ".[dev]"       # Editable install with dev deps

# Run
remix run song.mp3 --to-bitwig
remix analyze song.mp3 --visualize

# Test
pytest tests/ -v

# Lint
ruff check src/ tests/
```

## Important Implementation Notes

- **Demucs is invoked as a subprocess** (`python -m demucs ...`) rather than imported directly, because its internal API is unstable and it manages GPU memory aggressively.
- **Basic Pitch** is imported directly via `basic_pitch.inference.predict()`.
- **librosa.beat.beat_track** returns different shapes across versions — always handle both scalar and array return for `tempo`.
- The Bitwig Controller Extension uses **API version 18** (`loadAPI(18)`).
- OSC messages use **big-endian** byte order and strings are null-terminated + padded to 4-byte boundaries.
- All file paths should use `pathlib.Path` consistently.
- Print output uses colored terminal formatting — wrap in a `log` utility that respects `--quiet` flag.

## Reminders

- Keep the CLI user-friendly — this is a hobby tool, not enterprise software
- Prefer sensible defaults over configuration
- Every module should work standalone (importable without the CLI)
- Don't over-engineer error handling, but do catch common failures (missing audio file, Demucs not installed, Bitwig not running) with helpful messages
- The blueprint is the creative differentiator — make the analysis output genuinely useful for remixing decisions
