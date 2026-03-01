#!/usr/bin/env bash
# Install the Remix Pipeline Bitwig controller extension.
# Copies RemixPipeline.control.js to Bitwig's controller scripts folder.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
SOURCE="$PROJECT_DIR/src/bitwig/RemixPipeline.control.js"
DEST_DIR="$HOME/Documents/Bitwig Studio/Controller Scripts"

if [ ! -f "$SOURCE" ]; then
    echo "Error: Controller script not found at $SOURCE" >&2
    exit 1
fi

mkdir -p "$DEST_DIR"
cp "$SOURCE" "$DEST_DIR/RemixPipeline.control.js"

echo "Installed: $DEST_DIR/RemixPipeline.control.js"
echo ""
echo "Next steps:"
echo "  1. Open Bitwig Studio"
echo "  2. Go to Settings → Controllers"
echo "  3. Click 'Add controller manually'"
echo "  4. Select 'Remix Pipeline' → 'Remix Pipeline'"
echo "  5. Set MIDI input to 'IAC Driver Bus 1'"
echo "  6. Click 'Add'"
