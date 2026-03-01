# Remix Recipes

Pre-configured workflow presets for common remix scenarios.
Run `remix recipes --list` to see all available recipes.

---

## bootleg

**Description:** Full stem split + MIDI — rebuild in a new genre/tempo

Best for: Creating a full remix where you want all stems as MIDI references
to build something completely new.

```bash
remix recipes bootleg song.mp3 -o ./my_remix/
```

**What you get:**
- 6 stems (vocals, drums, bass, guitar, piano, other)
- MIDI transcription of all stems at medium sensitivity
- Blueprint JSON with key, BPM, chords, structure

**Settings:** `htdemucs_6s` model, medium sensitivity

---

## vocal-chop

**Description:** Extract vocals → MIDI melody reference + clean vocal stem

Best for: Vocal chop edits, acapella remixes, or using the vocal melody as a
MIDI guide to write new harmonies.

```bash
remix recipes vocal-chop song.mp3 -o ./vocal_edit/
```

**What you get:**
- Clean vocal stem (mdx_extra has best vocal separation)
- MIDI melody transcription at medium sensitivity
- Blueprint with key detection for pitch-matching

**Settings:** `mdx_extra` model, medium sensitivity

---

## drum-rack

**Description:** Isolate drums → MIDI pattern for Drum Machine Designer

Best for: Extracting the drum groove to build a new drum rack around,
or analyzing rhythmic patterns.

```bash
remix recipes drum-rack song.mp3 -o ./drum_edit/
```

**What you get:**
- Isolated drum stem
- MIDI drum pattern with low sensitivity (fewer false triggers)
- Blueprint with BPM and structure

**Settings:** `htdemucs` model (faster), low sensitivity

---

## lo-fi

**Description:** Extract piano/keys + drums for lo-fi hip-hop remixes

Best for: Creating lo-fi beats from existing tracks. High sensitivity captures
subtle piano runs and quiet drum hits.

```bash
remix recipes lo-fi song.mp3 -o ./lofi_remix/
```

**What you get:**
- All 6 stems including piano separation
- High sensitivity MIDI (captures more detail)
- Blueprint with energy arc analysis

**Settings:** `htdemucs_6s` model, high sensitivity

---

## acapella

**Description:** Best possible vocal isolation

Best for: When you just need the cleanest possible vocal stem, nothing else.
`mdx_extra` is optimized for vocal isolation quality.

```bash
remix recipes acapella song.mp3 -o ./acapella/
```

**What you get:**
- High quality vocal stem
- Instrumental (everything minus vocals)
- Blueprint for key/BPM reference

**Settings:** `mdx_extra` model, medium sensitivity

---

## stems-only

**Description:** Just separate stems, no MIDI conversion

Best for: When you want audio stems to mix/remix but don't need MIDI.
Fastest recipe — skips Basic Pitch transcription entirely.

```bash
remix recipes stems-only song.mp3 -o ./stems/
```

**What you get:**
- 6 stems (vocals, drums, bass, guitar, piano, other)
- Blueprint JSON
- No MIDI files

**Settings:** `htdemucs_6s` model, no transcription

---

## Custom Workflow Examples

**Override BPM for quantization:**
```bash
remix recipes bootleg song.mp3 --bpm 128
```

**Send directly to Bitwig:**
```bash
remix recipes bootleg song.mp3 --to-bitwig --play
```

**Full pipeline with visualization:**
```bash
remix run song.mp3 --visualize --to-bitwig
```

**Watch folder for automatic processing:**
```bash
remix watch ~/Dropbox/ToRemix/ ~/Remixes/
```
