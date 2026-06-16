# crewai-remotion

Agentic video production CLI that produces **vertical 9:16 social videos** from a **topic** + **brand profile** using a film-production crew pipeline (CrewAI + Remotion). Features real motion graphics, sound effects, voice-cloning TTS, and storyboard verification.

## Features

- **Motion Graphics Studio** — 9 programmatic graphic types (particles, waves, ring pulses, morphs, data flows, energy bursts, orbitals, grid pulses, text effects) with parallax depth and camera motion
- **Sound Effects** — timed SFX at cut points (whoosh, impact, swoosh) synced to transitions
- **Voice Cloning TTS** — trainable on your voice via F5-TTS (zero-shot) or ElevenLabs; Piper CPU fallback
- **Storyboard Verification** — mid-pipeline visual check using GPT-4o-mini vision before full render
- **13-crew pipeline** — Topic Research → Development → Writers Room → Asset Research → Visual Development → Creative Review → Clearance → Voice Director → Audio → Post-production → Storyboard Verification → QC → Render
- **Brand system** — YAML profiles with voice tone, visual identity, motion style, SFX preferences

## Prerequisites

- Python 3.11–3.13 (**required** — CrewAI does not support 3.14 yet; use `uv python install 3.13`)
- Node.js 18+ (for Remotion render)
- ffmpeg (optional — placeholder MP4 fallback)

## Setup

```bash
uv python install 3.13
uv venv --python 3.13 .venv
source .venv/bin/activate
uv pip install -e .

cp .env.example .env
# Required: OPENAI_API_KEY, SERPER_API_KEY (topic + image research)

cd remotion && npm install
```

## Quick start

Use the project wrapper (no venv activation required):

```bash
./crewai-remotion create --topic "Notion, Linear, Perplexity for SaaS founders" --non-interactive
```

Or activate the venv first:

```bash
source .venv/bin/activate
crewai-remotion create --topic "Notion, Linear, Perplexity for SaaS founders" --non-interactive
```

Or via uv:

```bash
uv run crewai-remotion create --topic "Notion, Linear, Perplexity for SaaS founders" --non-interactive

# Interactive brand wizard
./crewai-remotion brand init

# Plan only (no render)
./crewai-remotion plan --topic "3 AI tools every founder should use" --brand brands/default.brand.yaml --non-interactive

# Render existing spec
./crewai-remotion render --spec output/<run-id>/video_spec.json
```

## CLI commands

| Command | Description |
|---------|-------------|
| `create` | Full pipeline → MP4 + deliverables |
| `plan` | Artifacts only, no render |
| `brand init` | Interactive brand wizard |
| `brand list` / `brand use` | Manage active brand |
| `render` | Render from `video_spec.json` |
| `loop status` / `loop distill` | Flywheel tooling |

## Output layout

```
output/<run-id>/
├── video_spec.json
├── av_script.json
├── voice.wav
├── captions.json
├── video.mp4
├── storyboard/              # pre-render still frames for verification
├── assets/images/           # downloaded scene images
├── scene_image_manifest.json
├── deliverables/
└── traces/trace.jsonl
```

## Brand YAML

See `brands/default.brand.yaml` and `brands/schema.brand.yaml`. Per-brand assets live in `brands/<slug>/`.

## Architecture

- **Executive Producer Flow** (`main.py`) — CrewAI Flow wrapping all phases
- **CrewAI agents** (`crews/`) — topic, development, writers, asset research, visual development, creative review, clearance, voice director, postproduction, QC
- **Asset pipeline** — Serper image search → download → `remotion/public/runs/<run-id>/`
- **Gates** — approval checkpoints between phases (creative brief, hook selection, AV script, picture lock, storyboard verification, QC)
- **Remotion** — `SocialVertical` renders motion graphics, SFX, audio, and captions via TransitionSeries
- **Loop engineering** — trace capture + flywheel learnings in `loops/`

## Environment

| Variable | Purpose |
|----------|---------|
| `OPENAI_API_KEY` | **Required** — CrewAI agents + storyboard vision gate |
| `OPENAI_MODEL_NAME` | Agent model (default `gpt-4o-mini`) |
| `PIPER_VOICE` | Piper TTS voice (default `en_US-lessac-medium`) |
| `PIPER_DATA_DIR` | Where Piper models are cached (default `assets/piper-voices`) |
| `ELEVENLABS_API_KEY` | Optional — ElevenLabs cloud TTS with voice cloning |
| `SERPER_API_KEY` | Topic research + scene image search |
| `REMOTION_PROJECT_PATH` | Default `remotion` |

## TTS Providers

| Provider | Voice Cloning | Type | Setup |
|----------|--------------|------|-------|
| `piper` | No | Local CPU | Built-in (default) |
| `f5-tts` | Yes (zero-shot, 3-10s sample) | Local GPU/CPU | `uv pip install -e ".[tts-f5]"` |
| `elevenlabs` | Yes (cloud, instant clone) | Cloud API | `uv pip install -e ".[tts-elevenlabs]"` + set `ELEVENLABS_API_KEY` |

Set in `brands/<name>.brand.yaml`: `audio.tts_provider: f5-tts` and `audio.tts_clone_sample: path/to/voice.wav`.

## Sound Effects

SFX are cataloged in `assets/sfx/manifest.json` (8 built-in sounds: whoosh, impact, pop, click, etc.). The Sound Designer agent in postproduction chooses SFX per cut. Additional royalty-free sources: [freesound.org](https://freesound.org), [kenney.nl](https://kenney.nl), [pixabay.com/sound-effects](https://pixabay.com/sound-effects).
