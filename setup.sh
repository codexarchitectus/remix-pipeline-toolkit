#!/bin/bash
set -e

echo "Remix Pipeline Toolkit — Setup"
echo ""

# Python version check
python3 -c "import sys; assert sys.version_info >= (3, 10)" 2>/dev/null || {
    echo "Python 3.10+ required"
    echo "Install with: brew install python@3.12"
    exit 1
}

# FFmpeg check (required by Demucs for audio loading)
if ! command -v ffmpeg &>/dev/null; then
    echo "FFmpeg not found — installing via Homebrew..."
    if command -v brew &>/dev/null; then
        brew install ffmpeg
    else
        echo "Homebrew not found. Install FFmpeg manually: https://ffmpeg.org"
        echo "Or install Homebrew first: https://brew.sh"
        exit 1
    fi
fi

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

source .venv/bin/activate
pip install --quiet --upgrade pip
pip install -e ".[dev]"

echo ""
echo "Setup complete!"
echo ""
echo "  source .venv/bin/activate"
echo "  remix run song.mp3                # Full pipeline"
echo "  remix run song.mp3 --to-bitwig    # + send to Bitwig"
echo "  remix analyze song.mp3            # Analysis only"
echo "  remix --help                      # All commands"
echo ""
echo "Bitwig setup: see docs/BITWIG_SETUP.md"
