# Audio Edit Sync — VO-Primary, Music-Secondary

Voiceover is the primary cut clock. Music reinforces but never leads. Every cut references a specific audio event — never "it felt right."

## VO Sync Rules

### Cut Between Phrases, Not Mid-Word
- Use Whisper `word.start_ms` / `word.end_ms` for precise cut placement.
- Cut points live at phrase boundaries, not syllable breaks.
- If a phrase ends at frame 87 and the next begins at frame 92, the cut lives at 87–92.

### Keep ~30% of Natural Pauses
- Do not machine-gun VO — breaths and micro-pauses create rhythm.
- If TTS outputs 5 natural pauses in 30s, keep at least 2.
- Remove pauses only when they fall mid-beat and break retention curve.

### Emphasis Words
- VODirection marks `emphasis_words[]` per beat.
- Emphasis words may get a jump_cut punch-in 2 frames before the word lands.
- Accent shape or scale pop on emphasis word for visual reinforcement.

### J-Cut (Audio Leads)
- Audio from beat N+1 starts before visual changes to beat N+1.
- Set `split_edit: j_cut, audio_lead_frames: 3-8` on the incoming cut.
- Standard for hooks — VO teases before visual reveal.
- In Remotion: TransitionSeries sequence boundary offset — picture changes late, audio layer is continuous.

### L-Cut (Audio Trails)
- Outgoing VO continues after visual changes to next beat.
- Set `split_edit: l_cut, audio_trail_frames: 6-15`.
- Employs emotional carry: last word of beat N lands over beat N+1's visual.
- Use on explainer → proof, body → CTA transitions.

### Perceived Sync Offset
- Place visual cut 1–2 frames **early** relative to audio event.
- Human perception registers visual changes slightly after audio — this offset creates perceived sync.
- critical events (smash_cut, stat reveal): cut exactly on audio event.

## Music Sync Rules

### BPM Structure
- Analyze music track BPM before marking sync points.
- 120 BPM = 2 beats/sec = 1 beat every 15 frames at 30fps.
- SoundPlan outputs `sync_markers[]` with `frame, event, use_for`.

### Downbeat Mapping
- Major scene cuts on downbeats (beats 1 and 3 in 4/4 time).
- Accent overlays (color pop, scale punch, shape flash) on snare (beats 2 and 4).
- Do not cut every beat — 30s piece ≈ 4-8 major cuts, not 30 cut points.

### Music Ducking
- Duck music under VO: reduce music_volume to 0.08–0.15 during VO beats.
- Ramp ducking in/out over 6–12 frames — no hard gain changes.
- Full music volume only during: intro (before VO), transitions, end card.
- Ducking curve: `interpolate(currentFrame, [in, out], [0.25, 0.10], {extrapolateRight: 'clamp'})`.

### Speed Ramp Sync
- Kinetic text enters on music build (rising energy).
- Hold on verse (stable music section).
- Smash_cut on drop (energy peak).
- Beat-type to music energy mapping:
  - Hook: high energy, full music (no ducking yet)
  - Body points: mid energy, ducked under VO
  - Stat reveal: music spike on number
  - CTA: fade music out over last 2 seconds

## SFX Bridges

Sound Designer outputs `sfx_on_cuts[]` — one SFX per transition that needs it.

| Cut type | SFX | Timing |
|----------|-----|--------|
| slide / wipe | Short whoosh | Duck under VO; 4-6 frames |
| smash_cut | Impact hit | Hard sync on cut frame; optional 100ms silence pre-cut |
| match_cut | Subtle rise or none | Motion carries the edit |
| dissolve | Soft swell | Align with fade midpoint |
| hard_cut | None | Silence carries the cut |
| montage | Micro whoosh | Every 2-3 items, not every item |

## Caption-VO Sync

- Captions follow Whisper word timestamps exactly — never approximate.
- `createTikTokStyleCaptions({ combineTokensWithinMilliseconds: 800 })` groups words naturally.
- Caption highlight color (`caption_highlight`) pulses on emphasis words.
- Captions never overlap headline zone — if a beat has both, caption moves to lower third.

## Phrase Boundary Annotation

Voice Director marks `phrase_boundaries[]` in VODirection:

```json
{
  "phrase_boundaries": [
    {"beat_id": "b0", "phrase_end_frame_hint": 85},
    {"beat_id": "b1", "phrase_end_frame_hint": 170},
    ...
  ]
}
```

Editor uses these as initial cut anchors, then refines against actual Whisper timestamps.

## Agent Usage

- **Voice Director**: Marks `emphasis_words`, `pause_after_ms`, `phrase_boundaries` per beat.
- **Editor**: Primary cut authority — refines VODirection hints against real Whisper timestamps.
- **Sound Designer**: Maps music BPM → `sync_markers[]`; tags `sfx_on_cuts[]` per Editor's cut list.
- **Caption Designer**: Syncs to Whisper word timestamps; places captions outside headline zone.
- **Mograph TD**: Implements J/L split offsets in TransitionSeries; audio layer is continuous.
