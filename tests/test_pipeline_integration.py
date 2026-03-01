"""End-to-end integration test for the analysis pipeline.

Generates a synthetic audio fixture (10s 440Hz sine) and runs generate_blueprint()
to verify all required keys are present in the output.

Mark slow tests to skip by default:
    pytest tests/ -v -m "not slow"
    pytest tests/ -v -m slow   # run only slow tests
"""

import json
import tempfile
from pathlib import Path

import numpy as np
import pytest


def make_test_audio(path: Path, frequency: float = 440.0, sr: int = 22050, duration: float = 10.0):
    """Write a simple sine wave to a WAV file."""
    import soundfile as sf

    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    y = (np.sin(2 * np.pi * frequency * t) * 0.5).astype(np.float32)
    sf.write(str(path), y, sr)


@pytest.mark.slow
class TestGenerateBlueprintIntegration:
    """Full pipeline test — skipped by default (requires librosa, soundfile, etc.)"""

    def test_blueprint_has_required_keys(self, tmp_path):
        audio_path = tmp_path / "test_sine.wav"
        make_test_audio(audio_path)

        from src.analysis.blueprint import generate_blueprint

        bp = generate_blueprint(str(audio_path), str(tmp_path / "test.blueprint.json"))

        required_top_keys = [
            "_meta", "tempo", "key", "chord_progression", "structure",
            "structure_summary", "energy_profile", "frequency_balance",
            "duration_seconds", "remix_hints",
        ]
        for key in required_top_keys:
            assert key in bp, f"Blueprint missing top-level key: '{key}'"

    def test_blueprint_tempo_structure(self, tmp_path):
        audio_path = tmp_path / "test_sine.wav"
        make_test_audio(audio_path)

        from src.analysis.blueprint import generate_blueprint

        bp = generate_blueprint(str(audio_path), str(tmp_path / "test.blueprint.json"))

        assert "bpm" in bp["tempo"]
        assert "feel" in bp["tempo"]
        assert isinstance(bp["tempo"]["bpm"], float)

    def test_blueprint_key_structure(self, tmp_path):
        audio_path = tmp_path / "test_sine.wav"
        make_test_audio(audio_path)

        from src.analysis.blueprint import generate_blueprint

        bp = generate_blueprint(str(audio_path), str(tmp_path / "test.blueprint.json"))

        key = bp["key"]
        assert "key" in key
        assert "mode" in key
        assert "full" in key
        assert "confidence" in key
        assert "camelot" in key

    def test_blueprint_energy_structure(self, tmp_path):
        audio_path = tmp_path / "test_sine.wav"
        make_test_audio(audio_path)

        from src.analysis.blueprint import generate_blueprint

        bp = generate_blueprint(str(audio_path), str(tmp_path / "test.blueprint.json"))

        energy = bp["energy_profile"]
        assert "energy_curve" in energy
        assert "peak_energy_time" in energy
        assert "average_energy" in energy
        assert len(energy["energy_curve"]) == 64

    def test_blueprint_remix_hints(self, tmp_path):
        audio_path = tmp_path / "test_sine.wav"
        make_test_audio(audio_path)

        from src.analysis.blueprint import generate_blueprint

        bp = generate_blueprint(str(audio_path), str(tmp_path / "test.blueprint.json"))

        hints = bp["remix_hints"]
        assert "compatible_keys" in hints
        assert "half_time_bpm" in hints
        assert "double_time_bpm" in hints
        assert "energy_arc" in hints
        assert isinstance(hints["compatible_keys"], list)

    def test_blueprint_json_is_serializable(self, tmp_path):
        audio_path = tmp_path / "test_sine.wav"
        make_test_audio(audio_path)

        from src.analysis.blueprint import generate_blueprint

        bp_path = tmp_path / "test.blueprint.json"
        generate_blueprint(str(audio_path), str(bp_path))

        assert bp_path.exists()
        with open(bp_path) as f:
            loaded = json.load(f)
        assert "_meta" in loaded

    def test_blueprint_frequency_balance_sums_to_one(self, tmp_path):
        audio_path = tmp_path / "test_sine.wav"
        make_test_audio(audio_path)

        from src.analysis.blueprint import generate_blueprint

        bp = generate_blueprint(str(audio_path), str(tmp_path / "test.blueprint.json"))

        freq = bp["frequency_balance"]
        total = sum(freq.values())
        assert abs(total - 1.0) < 0.01, f"Frequency balance sums to {total}, expected ~1.0"
