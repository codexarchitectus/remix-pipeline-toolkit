# 🎛️ Remix Pipeline Toolkit

**Audio → Analysis → Stems → MIDI → Bitwig Studio** — in one command.

Drop a reference track in, get back a musical blueprint, separated stems, and MIDI files that auto-load into Bitwig Studio.

## Quick Start

```bash
./setup.sh && source .venv/bin/activate

remix run song.mp3                    # Full pipeline
remix run song.mp3 --to-bitwig        # + auto-load into Bitwig
remix analyze song.mp3 --visualize    # Just analyze
remix recipes bootleg song.mp3        # Use a preset
```

## What You Get

```
remix_output/SongName/
├── blueprint.json    ← Key, chords, structure, energy curve
├── stems/            ← Separated audio (6 stems)
├── midi/             ← MIDI files per stem
└── session_info.json ← BPM, metadata
```

## Commands

| Command | Description |
|---------|-------------|
| `remix run` | Full pipeline |
| `remix analyze` | Reference analysis only |
| `remix stems` | Stem separation only |
| `remix midi` | MIDI conversion only |
| `remix album` | Batch process a folder |
| `remix watch` | Auto-process dropped files |
| `remix recipes` | Pre-configured presets |
| `remix bitwig send` | Send to Bitwig |
| `remix bitwig install` | Install Bitwig controller |

## Docs

- [Bitwig Setup](docs/BITWIG_SETUP.md)
- [Recipes](docs/RECIPES.md)
- [CLAUDE.md](CLAUDE.md) — Full architecture & spec

## Dev

```bash
pip install -e ".[dev]"
pytest tests/ -v
ruff check src/ tests/
```
