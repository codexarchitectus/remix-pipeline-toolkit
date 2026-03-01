"""CLI entry point — all commands for the remix toolkit.

Usage:
    remix run song.mp3 [--to-bitwig] [--play]
    remix analyze song.mp3 [--visualize]
    remix stems song.mp3
    remix midi stems/ [--bpm 128]
    remix bitwig send ./output/Song/
    remix bitwig install
    remix watch ~/Dropbox/ ~/Remixes/
    remix recipes --list
"""

import sys
import time
from pathlib import Path

import click

from src.config import (
    DEMUCS_MODEL, DEMUCS_MODELS, AUDIO_EXTENSIONS,
    RECIPES, set_quiet, header, log, success, error,
)


@click.group()
@click.option("--quiet", is_flag=True, help="Suppress non-essential output.")
def cli(quiet):
    """Remix Pipeline Toolkit — Audio → Analysis → Stems → MIDI → Bitwig"""
    set_quiet(quiet)


# ── remix run ────────────────────────────────────────────────

@cli.command()
@click.argument("audio", type=click.Path(exists=True))
@click.option("-o", "--output", type=click.Path(), default=None, help="Output directory.")
@click.option("--model", type=click.Choice(list(DEMUCS_MODELS)), default=DEMUCS_MODEL, help="Demucs model.")
@click.option("--sensitivity", type=click.Choice(["low", "medium", "high"]), default="medium")
@click.option("--bpm", type=float, default=None, help="Override BPM detection.")
@click.option("--no-quantize", is_flag=True, help="Disable MIDI quantization.")
@click.option("--no-analyze", is_flag=True, help="Skip reference analysis.")
@click.option("--visualize", is_flag=True, help="Show ASCII energy/structure charts.")
@click.option("--to-bitwig", is_flag=True, help="Send output to Bitwig Studio.")
@click.option("--play", is_flag=True, help="Auto-play in Bitwig after loading.")
def run(audio, output, model, sensitivity, bpm, no_quantize, no_analyze, visualize, to_bitwig, play):
    """Full pipeline: analyze → separate → MIDI → [Bitwig]."""
    from src.pipeline.orchestrator import run_pipeline

    run_pipeline(
        audio_path=audio,
        output_dir=output,
        model=model,
        sensitivity=sensitivity,
        bpm_override=bpm,
        quantize=not no_quantize,
        analyze=not no_analyze,
        visualize=visualize,
        send_to_bitwig=to_bitwig,
        auto_play=play,
    )


# ── remix album ──────────────────────────────────────────────

@cli.command()
@click.argument("folder", type=click.Path(exists=True))
@click.option("-o", "--output", type=click.Path(), default="./remix_output")
@click.option("--model", type=click.Choice(list(DEMUCS_MODELS)), default=DEMUCS_MODEL)
@click.option("--sensitivity", type=click.Choice(["low", "medium", "high"]), default="medium")
@click.option("--to-bitwig", is_flag=True)
def album(folder, output, model, sensitivity, to_bitwig):
    """Process every audio file in a folder."""
    from src.pipeline.orchestrator import run_album

    run_album(folder, output, model=model, sensitivity=sensitivity, send_to_bitwig=to_bitwig)


# ── remix analyze ────────────────────────────────────────────

@cli.command()
@click.argument("audio", type=click.Path(exists=True))
@click.option("-o", "--output", type=click.Path(), default=None, help="Blueprint output path.")
@click.option("--visualize", is_flag=True, help="Show ASCII energy/structure charts.")
def analyze(audio, output, visualize):
    """Analyze a reference track → blueprint JSON."""
    from src.analysis.blueprint import generate_blueprint

    bp = generate_blueprint(audio, output, visualize=visualize)
    click.echo(f"\n  BPM: {bp['tempo']['bpm']}  Key: {bp['key']['full']}  "
               f"Structure: {bp['structure_summary']}")


# ── remix stems ──────────────────────────────────────────────

@cli.command()
@click.argument("audio", type=click.Path(exists=True))
@click.option("-o", "--output", type=click.Path(), default="./remix_output/stems")
@click.option("--model", type=click.Choice(list(DEMUCS_MODELS)), default=DEMUCS_MODEL)
def stems(audio, output, model):
    """Separate audio into stems only (no MIDI)."""
    from src.pipeline.separator import separate_stems

    result = separate_stems(audio, output, model=model)
    if result:
        success(f"Stems saved: {result}")


# ── remix midi ───────────────────────────────────────────────

@cli.command()
@click.argument("stems_dir", type=click.Path(exists=True))
@click.option("-o", "--output", type=click.Path(), default="./remix_output/midi")
@click.option("--bpm", type=float, default=120.0, help="BPM for quantization.")
@click.option("--sensitivity", type=click.Choice(["low", "medium", "high"]), default="medium")
@click.option("--no-quantize", is_flag=True)
def midi(stems_dir, output, bpm, sensitivity, no_quantize):
    """Convert stems to MIDI (skip separation)."""
    from src.pipeline.transcriber import transcribe_stems
    from src.pipeline.quantizer import process_midi_files

    midi_files = transcribe_stems(stems_dir, output, sensitivity=sensitivity)
    if not no_quantize:
        process_midi_files(midi_files, bpm=bpm)
    success(f"{len(midi_files)} MIDI files created in {output}")


# ── remix bitwig ─────────────────────────────────────────────

@cli.group()
def bitwig():
    """Bitwig Studio integration commands."""
    pass


@bitwig.command()
@click.argument("output_dir", type=click.Path(exists=True))
@click.option("--play", is_flag=True)
def send(output_dir, play):
    """Send pipeline output to Bitwig Studio."""
    from src.bitwig.bridge import BitwigBridge

    bw = BitwigBridge()
    bw.create_session_from_pipeline(output_dir)
    if play:
        time.sleep(2)
        bw.play()
    bw.close()


@bitwig.command()
def install():
    """Install the Bitwig controller extension."""
    from src.config import get_bitwig_controller_dir
    import shutil

    src = Path(__file__).parent / "bitwig" / "RemixPipeline.control.js"
    dest_dir = get_bitwig_controller_dir()
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / "RemixPipeline.control.js"

    if not src.exists():
        error(f"Controller script not found at {src}")
        return

    shutil.copy2(src, dest)
    success(f"Installed: {dest}")
    click.echo("  → In Bitwig: Settings → Controllers → Add → Remix Pipeline")


# ── remix watch ──────────────────────────────────────────────

@cli.command()
@click.argument("input_dir", type=click.Path(exists=True))
@click.argument("output_dir", type=click.Path(), default="./remix_output")
@click.option("--model", default=DEMUCS_MODEL)
@click.option("--sensitivity", default="medium")
@click.option("--interval", type=int, default=5, help="Poll interval in seconds.")
def watch(input_dir, output_dir, model, sensitivity, interval):
    """Watch a folder and auto-process new audio files."""
    from src.pipeline.orchestrator import run_pipeline

    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    processed_file = input_dir / ".remix_processed"
    processed = set()

    if processed_file.exists():
        processed = set(processed_file.read_text().strip().split("\n"))

    header("WATCH MODE")
    log(f"Watching: {input_dir}")
    log(f"Output:   {output_dir}")
    click.echo("  Drop audio files in to auto-process. Ctrl+C to stop.\n")

    try:
        while True:
            for f in input_dir.iterdir():
                if f.suffix.lower() in AUDIO_EXTENSIONS and f.name not in processed:
                    log(f"New file: {f.name}")
                    run_pipeline(str(f), str(output_dir), model=model, sensitivity=sensitivity)
                    processed.add(f.name)
                    with open(processed_file, "a") as pf:
                        pf.write(f"{f.name}\n")
            time.sleep(interval)
    except KeyboardInterrupt:
        click.echo("\nWatch stopped.")


# ── remix recipes ────────────────────────────────────────────

@cli.command()
@click.argument("recipe", required=False, type=click.Choice(list(RECIPES)))
@click.argument("audio", required=False, type=click.Path(exists=True))
@click.option("--list", "list_recipes", is_flag=True, help="Show available recipes.")
@click.option("-o", "--output", type=click.Path(), default=None)
@click.option("--bpm", type=float, default=None)
def recipes(recipe, audio, list_recipes, output, bpm):
    """Pre-configured workflow presets."""
    if list_recipes or not recipe:
        click.echo("\nRemix Recipes:\n")
        for name, info in RECIPES.items():
            click.echo(f"  {name:<14} — {info['description']}")
        click.echo(f"\n  Usage: remix recipes <recipe> <audio_file>")
        return

    if not audio:
        error("Provide an audio file: remix recipes {recipe} song.mp3")
        return

    info = RECIPES[recipe]
    from src.pipeline.orchestrator import run_pipeline

    run_pipeline(
        audio_path=audio,
        output_dir=output,
        model=info["model"],
        sensitivity=info["sensitivity"],
        bpm_override=bpm,
    )


if __name__ == "__main__":
    cli()
