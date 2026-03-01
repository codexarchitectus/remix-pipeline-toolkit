#!/bin/bash
set -e

echo "🎛️  Remix Pipeline Toolkit — Setup"
echo ""

python3 -c "import sys; assert sys.version_info >= (3, 10)" 2>/dev/null || {
    echo "❌ Python 3.10+ required"; exit 1
}

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev]"

echo ""
echo "✓ Setup complete!"
echo ""
echo "  source .venv/bin/activate"
echo "  remix run song.mp3                # Full pipeline"
echo "  remix run song.mp3 --to-bitwig    # + send to Bitwig"
echo "  remix analyze song.mp3            # Analysis only"
echo "  remix --help                      # All commands"
