# Bitwig Studio Setup Guide

## Prerequisites

- Bitwig Studio 5.3.13 or later (Controller API v18)
- macOS with IAC Driver enabled

## Step 1: Enable the IAC Driver

The IAC (Inter-Application Communication) Driver creates a virtual MIDI port that
Python uses to stream MIDI stems directly into Bitwig.

1. Open **Audio MIDI Setup** (Applications → Utilities)
2. Go to **Window → Show MIDI Studio**
3. Double-click **IAC Driver**
4. Check **Device is online**
5. Ensure at least one port exists (default: "Bus 1")

## Step 2: Install the Controller Extension

Run the install script from the project root:

```bash
./scripts/install_bitwig_controller.sh
```

Or use the CLI:

```bash
remix bitwig install
```

This copies `RemixPipeline.control.js` to:
```
~/Documents/Bitwig Studio/Controller Scripts/
```

## Step 3: Add the Controller in Bitwig

1. Open Bitwig Studio
2. Go to **Settings → Controllers**
3. Click **Add controller manually**
4. Select **Remix Pipeline → Remix Pipeline**
5. Set MIDI Input to **IAC Driver Bus 1**
6. Click **Add**

The controller status should show green (active).

## Step 4: Verify the Connection

In Bitwig's controller log (Settings → Controllers → click the controller → View log),
you should see:

```
Remix Pipeline controller ready — OSC port 8000
```

## Using the Automated Recording Flow

Run the full pipeline with `--to-bitwig`:

```bash
remix run song.mp3 --to-bitwig --play
```

**What happens:**

1. Python analyzes the track, separates stems, converts to MIDI
2. Sends `/remix/build` OSC → Bitwig creates 6 instrument tracks, arms them, starts recording
3. Python waits 3 seconds for Bitwig to be ready
4. Python streams all 6 MIDI stems simultaneously via IAC Driver Bus 1
5. Each stem lands on its correct track (via MIDI channel routing):
   - Ch 1 (0-indexed 0) → Vocals
   - Ch 2 (0-indexed 1) → Bass
   - Ch 3 (0-indexed 2) → Guitar
   - Ch 4 (0-indexed 3) → Piano
   - Ch 5 (0-indexed 4) → Other
   - Ch 10 (0-indexed 9) → Drums
6. Sends `/remix/done` → Bitwig stops recording, rewinds to bar 1, plays

## OSC API Reference

The controller listens on UDP port 8000:

| Address | Arguments | Description |
|---------|-----------|-------------|
| `/remix/build` | `<manifest_path: str>` | Create tracks, arm, start recording |
| `/remix/done` | — | Stop recording, rewind, play |
| `/remix/play` | — | Start transport |
| `/remix/stop` | — | Stop transport |
| `/remix/bpm` | `<bpm: float>` | Set tempo |
| `/remix/mute` | `<stem: str> <muted: bool>` | Mute/unmute a track |
| `/remix/solo` | `<stem: str> <soloed: bool>` | Solo/unsolo a track |
| `/remix/volume` | `<stem: str> <vol: float>` | Set track volume (0.0–1.0) |

## API Version Compatibility

- **Target:** Controller API v18 (Bitwig 5.3.13+)
- **Bitwig 6.0 beta:** Compatible. The `NoteInput`, `Track`, `Transport`, and
  `Application` APIs used here are stable across both versions. No changes needed.
- **Bitwig 5.0–5.2:** Not tested. API v18 was introduced in 5.x — check your
  Bitwig version if the controller fails to load.

## Troubleshooting

**"IAC Driver port not found"**
- Ensure IAC Driver is enabled in Audio MIDI Setup (Step 1)
- Restart Bitwig after enabling the driver

**Controller shows "inactive" in Bitwig**
- Check that the JS file was copied correctly: `ls ~/Documents/Bitwig\ Studio/Controller\ Scripts/`
- Re-add the controller (remove old entry first)

**Tracks not being created**
- Check Bitwig's controller log for errors
- Ensure `/remix/build` OSC is reaching port 8000 (check firewall settings)

**MIDI stems empty after recording**
- The IAC Driver was not active during playback
- Verify `mido` is installed: `pip install 'mido[ports-rtmidi]>=1.3'`
- Check that the IAC port name matches: `python -c "from src.bitwig.midi_player import list_iac_ports; print(list_iac_ports())"`
