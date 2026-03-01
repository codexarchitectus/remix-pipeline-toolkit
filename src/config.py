"""Shared configuration, constants, and sensitivity presets."""

from pathlib import Path

# ── Audio ────────────────────────────────────────────────────

AUDIO_EXTENSIONS = {".mp3", ".wav", ".flac", ".aiff", ".aif", ".m4a", ".ogg"}
SAMPLE_RATE = 44100

# ── Demucs ───────────────────────────────────────────────────

DEMUCS_MODEL = "htdemucs_6s"  # 6 stems: vocals, drums, bass, guitar, piano, other
DEMUCS_MODELS = {
    "htdemucs":     {"stems": 4, "description": "Fast — vocals, drums, bass, other"},
    "htdemucs_6s":  {"stems": 6, "description": "Detailed — vocals, drums, bass, guitar, piano, other"},
    "mdx_extra":    {"stems": 4, "description": "Better vocal isolation"},
    "mdx_extra_q":  {"stems": 4, "description": "Highest quality, slowest"},
}

# ── MIDI Conversion ──────────────────────────────────────────

MIDI_ONSET_THRESHOLD = 0.5
MIDI_MIN_NOTE_LENGTH = 58  # ms
MIDI_MIN_FREQUENCY = 32    # Hz
MIDI_MAX_FREQUENCY = 4200  # Hz
QUANTIZE_RESOLUTION = 16   # 1/16th notes

SENSITIVITY_PRESETS = {
    "low":    {"onset_threshold": 0.7, "min_note_length": 80},
    "medium": {"onset_threshold": 0.5, "min_note_length": 58},
    "high":   {"onset_threshold": 0.3, "min_note_length": 40},
}

# ── GM Instrument Mapping ────────────────────────────────────

STEM_MIDI_PROGRAMS = {
    "vocals":  {"program": 54, "channel": 0,  "name": "Synth Voice",      "is_drum": False},
    "drums":   {"program": 0,  "channel": 9,  "name": "Standard Drums",   "is_drum": True},
    "bass":    {"program": 33, "channel": 1,  "name": "Electric Bass",    "is_drum": False},
    "guitar":  {"program": 25, "channel": 2,  "name": "Acoustic Guitar",  "is_drum": False},
    "piano":   {"program": 0,  "channel": 3,  "name": "Grand Piano",      "is_drum": False},
    "other":   {"program": 48, "channel": 4,  "name": "String Ensemble",  "is_drum": False},
}

# ── Bitwig ───────────────────────────────────────────────────

BITWIG_OSC_HOST = "127.0.0.1"
BITWIG_OSC_PORT = 8000

def get_bitwig_import_dir() -> Path:
    """Default directory the Bitwig controller watches for new sessions."""
    return Path.home() / "Documents" / "Bitwig Studio" / "Remix Pipeline"

def get_bitwig_controller_dir() -> Path:
    """Bitwig's controller scripts folder."""
    return Path.home() / "Documents" / "Bitwig Studio" / "Controller Scripts"

# ── Recipes ──────────────────────────────────────────────────

RECIPES = {
    "bootleg": {
        "description": "Full stem split + MIDI — rebuild in a new genre/tempo",
        "model": "htdemucs_6s",
        "sensitivity": "medium",
    },
    "vocal-chop": {
        "description": "Extract vocals → MIDI melody reference + clean vocal stem",
        "model": "mdx_extra",
        "sensitivity": "medium",
    },
    "drum-rack": {
        "description": "Isolate drums → MIDI pattern for Drum Machine Designer",
        "model": "htdemucs",
        "sensitivity": "low",
    },
    "lo-fi": {
        "description": "Extract piano/keys + drums for lo-fi hip-hop remixes",
        "model": "htdemucs_6s",
        "sensitivity": "high",
    },
    "acapella": {
        "description": "Best possible vocal isolation",
        "model": "mdx_extra",
        "sensitivity": "medium",
    },
    "stems-only": {
        "description": "Just separate stems, no MIDI conversion",
        "model": "htdemucs_6s",
        "sensitivity": "medium",
    },
}

# ── Terminal Colors ──────────────────────────────────────────

class Color:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    END = "\033[0m"


_quiet = False


def set_quiet(quiet: bool):
    global _quiet
    _quiet = quiet


def log(msg: str, color: str = Color.CYAN):
    if not _quiet:
        print(f"{color}▸ {msg}{Color.END}")


def header(msg: str):
    if not _quiet:
        print(f"\n{Color.BOLD}{Color.HEADER}{'═' * 60}")
        print(f"  {msg}")
        print(f"{'═' * 60}{Color.END}\n")


def success(msg: str):
    if not _quiet:
        print(f"{Color.GREEN}✓ {msg}{Color.END}")


def warn(msg: str):
    if not _quiet:
        print(f"{Color.YELLOW}⚠ {msg}{Color.END}")


def error(msg: str):
    print(f"{Color.RED}✗ {msg}{Color.END}")
