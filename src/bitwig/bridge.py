"""Python → Bitwig Studio bridge via OSC and file-based import.

Two integration paths:
  1. File-based (primary): Write MIDI + manifest → Bitwig controller auto-imports.
  2. OSC (secondary): Real-time control — play/stop/mute/solo/volume/bpm.
  3. IAC MIDI recording: Stream all stems simultaneously via IAC Driver while Bitwig records.
"""

from __future__ import annotations

import json
import shutil
import socket
import time
from pathlib import Path

from src.config import BITWIG_OSC_HOST, BITWIG_OSC_PORT, get_bitwig_import_dir, log, success, error
from src.bitwig.osc import build_message


class BitwigBridge:
    """Interface between the remix pipeline and Bitwig Studio."""

    def __init__(
        self,
        host: str = BITWIG_OSC_HOST,
        port: int = BITWIG_OSC_PORT,
        import_dir: Path | None = None,
    ):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.import_dir = import_dir or get_bitwig_import_dir()
        self.import_dir.mkdir(parents=True, exist_ok=True)

    def _send(self, address: str, *args):
        try:
            msg = build_message(address, *args)
            self.sock.sendto(msg, (self.host, self.port))
        except Exception as e:
            log(f"OSC send failed: {e}")

    # ── Session Building ─────────────────────────────────────

    def create_session_from_pipeline(self, pipeline_output_dir: str | Path) -> bool:
        """Copy MIDI + stems + manifest to Bitwig's import directory, then stream
        all stems via IAC Driver so Bitwig records each on its own track in one pass.

        Flow:
          1. Copy files + write manifest
          2. Send /remix/build OSC → Bitwig creates tracks, arms them, starts recording
          3. Wait 3s for Bitwig to be ready
          4. Stream all MIDI stems via IAC Driver in real-time
          5. Send /remix/done → Bitwig stops, rewinds, plays
        """
        output_dir = Path(pipeline_output_dir)
        info_path = output_dir / "session_info.json"

        if not info_path.exists():
            error(f"No session_info.json in {output_dir}")
            return False

        with open(info_path) as f:
            session = json.load(f)

        track_name = session["track"]
        bpm = session.get("bpm", 120)
        log(f"Sending to Bitwig: {track_name} @ {bpm} BPM")

        session_dir = self.import_dir / track_name
        session_dir.mkdir(parents=True, exist_ok=True)

        # Copy MIDI files
        midi_dir = output_dir / "midi"
        midi_files = []
        if midi_dir.exists():
            for f in midi_dir.glob("*.mid"):
                dest = session_dir / f.name
                shutil.copy2(f, dest)
                midi_files.append(dest)
                success(f"  {f.stem}.mid → Bitwig")

        # Copy stems
        for stems_candidate in output_dir.glob("stems/**/"):
            for f in stems_candidate.glob("*"):
                if f.suffix.lower() in {".mp3", ".wav", ".flac"}:
                    dest = session_dir / "stems"
                    dest.mkdir(exist_ok=True)
                    shutil.copy2(f, dest / f.name)

        # Write manifest for controller
        manifest = {
            "track": track_name,
            "bpm": bpm,
            "midi_files": [f.name for f in session_dir.glob("*.mid")],
            "ready": True,
            "timestamp": time.time(),
        }
        manifest_path = session_dir / "manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        # Tell Bitwig to create tracks, arm, and start recording
        self._send("/remix/build", str(manifest_path))
        self._send("/remix/bpm", float(bpm))

        if midi_files:
            # Wait for Bitwig to set up tracks and start recording
            log("Waiting for Bitwig to arm tracks (3s)...")
            time.sleep(3)

            # Stream all stems simultaneously via IAC Driver
            self.record_stems(midi_files)

            # Signal Bitwig to stop recording, rewind, play
            self._send("/remix/done")

        success(f"Session ready: {session_dir}")
        return True

    def record_stems(self, midi_files: list[Path], port_name: str = "IAC Driver Bus 1") -> None:
        """Stream MIDI stem files through the IAC Driver for Bitwig to record.

        Plays all stems simultaneously, preserving channel assignments so each
        stem lands on the correct Bitwig track.
        """
        from src.bitwig.midi_player import play_stems_to_iac

        log(f"Streaming {len(midi_files)} stems via {port_name}...")
        try:
            play_stems_to_iac(midi_files, port_name=port_name)
            success("MIDI playback complete")
        except Exception as e:
            error(f"IAC playback failed: {e}")
            log("Bitwig tracks may be empty — import MIDI files manually")

    # ── Playback ─────────────────────────────────────────────

    def play(self):
        self._send("/remix/play")

    def stop(self):
        self._send("/remix/stop")

    def set_bpm(self, bpm: float):
        self._send("/remix/bpm", float(bpm))

    # ── Track Control ────────────────────────────────────────

    def mute_track(self, stem_name: str, muted: bool = True):
        self._send("/remix/mute", stem_name, muted)

    def solo_track(self, stem_name: str, soloed: bool = True):
        self._send("/remix/solo", stem_name, soloed)

    def set_volume(self, stem_name: str, volume: float):
        self._send("/remix/volume", stem_name, float(volume))

    def close(self):
        self.sock.close()
