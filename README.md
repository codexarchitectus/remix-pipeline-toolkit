# Remix Pipeline Toolkit

**Audio → Analysis → Stems → MIDI → Bitwig Studio** — in one command.

Drop a reference track in, get back a musical blueprint, separated stems, MIDI files, and an automatically recorded Bitwig session.

```bash
remix run song.mp3 --to-bitwig --play
```

---

## What it does

1. **Analyzes** the track's musical DNA — key, chords, structure, BPM, energy curve
2. **Separates** it into 6 stems (vocals, drums, bass, guitar, piano, other) via [Demucs](https://github.com/facebookresearch/demucs)
3. **Converts** each stem to MIDI via [Basic Pitch](https://github.com/spotify/basic-pitch)
4. **Builds a Bitwig session** — streams all stems simultaneously through the IAC Driver while Bitwig records each on its own track, then rewinds and plays

The goal is a remix workflow: drop a track in → get a blueprint + stems + MIDI → use that as scaffolding to build something new.

---

## Requirements

- **Python 3.10+** — install via `brew install python@3.12`
- **FFmpeg** — install via `brew install ffmpeg` (required by Demucs for audio loading)
- **macOS IAC Driver** — for the Bitwig recording flow (built-in, just needs enabling)

## Quick Start

```bash
# Install Homebrew dependencies first (one-time)
brew install python@3.12 ffmpeg

# Then install the toolkit
./setup.sh
source .venv/bin/activate

# Full pipeline
remix run song.mp3

# Full pipeline + send to Bitwig
remix run song.mp3 --to-bitwig --play

# Analysis only
remix analyze song.mp3 --visualize

# Use a preset
remix recipes bootleg song.mp3
```

---

## Output

```
remix_output/SongName/
├── blueprint.json      ← Key, BPM, chords, structure, energy arc, remix hints
├── stems/              ← 6 separated audio stems
├── midi/               ← MIDI file per stem (quantized, GM program assigned)
└── session_info.json   ← Metadata
```

Example blueprint:
```json
{
  "tempo": { "bpm": 124.0, "feel": "upbeat / dance" },
  "key": { "key": "A", "mode": "minor", "full": "A minor", "camelot": "8A" },
  "chord_progression": [
    { "chord": "Am", "time": 0.0 },
    { "chord": "F",  "time": 2.4 },
    { "chord": "C",  "time": 4.8 }
  ],
  "remix_hints": {
    "compatible_keys": ["A minor (original)", "C major", "D minor"],
    "half_time_bpm": 62.0,
    "energy_arc": "build → peak → fade (classic arc)"
  }
}
```

---

## Commands

| Command | Description |
|---------|-------------|
| `remix run <audio>` | Full pipeline — analyze → stems → MIDI → [Bitwig] |
| `remix analyze <audio>` | Reference analysis → blueprint JSON |
| `remix stems <audio>` | Stem separation only |
| `remix midi <stems_dir>` | MIDI conversion only |
| `remix album <folder>` | Batch process a folder of tracks |
| `remix watch <input> <output>` | Auto-process files dropped into a folder |
| `remix recipes [--list] [recipe] <audio>` | Pre-configured workflow presets |
| `remix bitwig send <output_dir>` | Send pipeline output to Bitwig |
| `remix bitwig install` | Install the Bitwig controller extension |

### Options

```bash
remix run song.mp3 \
  --model htdemucs_6s   \  # Demucs model (default: htdemucs_6s)
  --sensitivity medium  \  # MIDI sensitivity: low / medium / high
  --bpm 128             \  # Override BPM detection
  --no-quantize         \  # Skip MIDI quantization
  --visualize           \  # Print ASCII energy/structure chart
  --to-bitwig           \  # Send to Bitwig Studio
  --play                    # Auto-play after loading
```

### Recipes

```bash
remix recipes --list

remix recipes bootleg    song.mp3   # Full stems + MIDI, rebuild everything
remix recipes vocal-chop song.mp3   # Clean vocal stem + melody MIDI
remix recipes drum-rack  song.mp3   # Drum stem + MIDI pattern
remix recipes lo-fi      song.mp3   # Piano + drums, high sensitivity
remix recipes acapella   song.mp3   # Best-quality vocal isolation
remix recipes stems-only song.mp3   # Stems only, no MIDI
```

---

## Bitwig Integration

The automated recording flow requires:
- **macOS IAC Driver** enabled (Audio MIDI Setup → MIDI Studio → IAC Driver → Device is online)
- **Controller extension** installed (`remix bitwig install`)
- **Bitwig 5.3.13+** with the Remix Pipeline controller active

When you run `remix run song.mp3 --to-bitwig`:
1. Python sends `/remix/build` → Bitwig creates 6 instrument tracks, arms them, starts recording
2. Python streams all 6 MIDI stems simultaneously via the IAC Driver
3. Each stem lands on its own track via MIDI channel routing
4. Python sends `/remix/done` → Bitwig stops, rewinds to bar 1, plays

See [docs/BITWIG_SETUP.md](docs/BITWIG_SETUP.md) for full setup instructions.

---

## Tech Stack

| Tool | Role |
|------|------|
| [Demucs](https://github.com/facebookresearch/demucs) (`htdemucs_6s`) | Stem separation |
| [Basic Pitch](https://github.com/spotify/basic-pitch) | Audio → MIDI |
| [librosa](https://librosa.org) | BPM, key, chords, structure, energy |
| [pretty_midi](https://github.com/craffel/pretty-midi) | MIDI quantization + GM programs |
| [mido](https://mido.readthedocs.io) | Real-time MIDI playback via IAC Driver |
| [Click](https://click.palletsprojects.com) | CLI |
| Bitwig Controller API v18 | Session automation (JS controller extension) |

---

## Dev

```bash
pip install -e ".[dev]"

# Tests (no audio hardware needed)
pytest tests/ -v -m "not slow"

# Full integration tests
pytest tests/ -v -m slow

# Lint
ruff check src/ tests/
```

---

## Docs

- [Bitwig Setup Guide](docs/BITWIG_SETUP.md)
- [Recipes Reference](docs/RECIPES.md)
