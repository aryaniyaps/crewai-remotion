# Cinematic Cuts — 9:16 Social Video Grammar

Motion graphics social video inherits editorial grammar from live-action: cuts control pace, meaning, and retention. Always specify **cut type + where + what audio event** — never "use a nice transition."

Sources: Adobe cuts guide, Vimeo J/L cuts, Motion Array cut types, beat-sync editing practice, Remotion TransitionSeries.

## Cut Taxonomy

### hard_cut
- **Narrative purpose**: Reset attention; new idea or topic shift.
- **When in 9:16**: Hook → body, CTA beat, stat reveal, between unrelated body points.
- **Audio sync rule**: Cut on phrase end or music downbeat (major beats only). Never mid-word.
- **Transition**: 2-4 frame fade; `linearTiming`.

### jump_cut
- **Narrative purpose**: Compress time; urgency; punch-in emphasis.
- **When in 9:16**: Tighten VO within same visual family; "3 points" rapid fire; emphasis word punch.
- **Audio sync rule**: Cut on word or breath; optional 5–10% scale punch on incoming beat. 2 frames before emphasis word lands.
- **Transition**: Slide same direction + in-beat scale punch; `springTiming` snappy (damping=20, stiffness=200).

### match_cut
- **Narrative purpose**: Visual continuity; symbolic link between ideas.
- **When in 9:16**: Match shape/motion between beats (circle→circle, slide direction continues).
- **Audio sync rule**: Cut at motion peak (cut-on-action) so movement masks the edit — ~70% of exit anim.
- **Transition**: Slide direction matches exit motion vector; `springTiming` smooth (damping=30, stiffness=120).

### smash_cut
- **Narrative purpose**: Shock; tonal whiplash; comedy; energy spike.
- **When in 9:16**: Hook payoff → calm explainer; loud kinetic → silent hold.
- **Audio sync rule**: Pair with silence dip or impact SFX. Never smash without audio contrast. Max 1 per 30s.
- **Transition**: Wipe fast (4-8 frames) + overlay flash/impact; `linearTiming` short.

### cut_on_action
- **Narrative purpose**: Hide the edit inside motion.
- **When in 9:16**: Transition during headline exit, illustration fly-in, camera push — not at rest.
- **Audio sync rule**: Align cut frame to peak velocity of outgoing motion (~70% of exit anim).
- **Transition**: Match exit vector; identical enter/exit vectors if invisible_cut variant.

### j_cut
- **Narrative purpose**: Anticipation; pull viewer into next beat before they see it.
- **When in 9:16**: Next beat's VO starts 3–8 frames before visual changes. Standard for hooks.
- **Audio sync rule**: Audio from beat N+1 leads; visual still on beat N. `split_edit: j_cut, audio_lead_frames: 3-8`.
- **Transition**: Audio continuous; visual transition at phrase boundary of next beat's VO.

### l_cut
- **Narrative purpose**: Flow; emotional carry; let outgoing idea linger.
- **When in 9:16**: Outgoing VO continues 6–15 frames over incoming visual. Explain → proof transitions.
- **Audio sync rule**: `split_edit: l_cut, audio_trail_frames: 6-15`. Keeps energy across calm→kinetic.
- **Transition**: Audio from beat N trails; visual changes before audio ends.

### cross_cut
- **Narrative purpose**: Parallel ideas; compare/contrast; tension.
- **When in 9:16**: Compare two options, before/after, problem/solution alternation. Max 2 alternations per 30s.
- **Audio sync rule**: Alternate beats on snare or phrase pairs.
- **Transition**: `hard_cut` or `slide` alternation.

### montage
- **Narrative purpose**: Condense progression; rapid information.
- **When in 9:16**: "5 steps" / stat flurry / feature list. 2-5 items in ≤8s.
- **Audio sync rule**: Downbeat every 2–4 beats — not every beat (avoids frantic feel). Items 3-6 frames each.
- **Transition**: Hard cut or micro slide; `linearTiming` 3-6 frames.

### dissolve
- **Narrative purpose**: Time pass; mood soften; section change.
- **When in 9:16**: Section changes (setup → payoff), emotional deceleration, CTA entrance.
- **Audio sync rule**: Align dissolve midpoint to music phrase boundary or VO breath pause.
- **Transition**: Fade 12–20 frames; `linearTiming` + ease.

### invisible_cut
- **Narrative purpose**: Seamless one-take feel; continuous motion.
- **When in 9:16**: Continuous kinetic typography with matched motion vectors.
- **Audio sync rule**: Audio continuous; no break in VO or music.
- **Transition**: Fade 1 frame + matched motion vectors; `CameraMotionBlur` on both beats; composed progress.

## Beat-Type → Cut Recommendations

| Beat role | Cut in | Cut out | Split edit |
|-----------|--------|---------|------------|
| Hook (0-3s) | j_cut (VO leads) or smash_cut from black | hard_cut or jump_cut on payoff word | J-cut in |
| Re-hook (~8s) | match_cut or cut_on_action | hard_cut | L-cut out optional |
| Body point | hard_cut or match_cut | hard_cut | None or L-cut |
| Stat / list montage | montage rhythm | jump_cut between items | None |
| Proof / demo | cross_cut if comparing | dissolve if mood shift | L-cut |
| CTA | dissolve or hard_cut in | Hold — no cut out | L-cut trail into end card |

## Default Rhythm (30s vertical)

```
j_cut → Hook (3s) → hard_cut → Point 1 (6s) → match_cut → Point 2 (6s) → hard_cut → Point 3 (6s) → l_cut → CTA (4s) → hold
```

- Hook opens with J-cut: VO leads by 4-6 frames, then visual reveals.
- Smash cut maximum 1 per 30s.
- Not every beat boundary gets a fancy cut — most are hard_cut or match_cut.
- CTA trails with L-cut: visual holds on end card while last VO line finishes.

## Dual Sync Axes

**VO-primary**: Whisper word timestamps are the primary cut clock.
**Music-secondary**: SoundPlan sync_markers reinforce major cuts on downbeats.

- Cut between phrases, not mid-word.
- Keep ~30% of natural pauses; don't machine-gun VO.
- Perceived sync: place visual cut 1–2 frames early relative to audio peak.
- Music downbeats (beats 1/3 in 4/4) for major scene cuts; snares (2/4) for accents.
- 30s piece ≈ 4-8 major cuts, not 30.

## SFX Bridges

| Cut type | SFX |
|----------|-----|
| slide / wipe transition | Short whoosh (ducked under VO) |
| smash_cut | Impact hit + optional 100ms silence pre-cut |
| match_cut | Subtle rise or none — motion carries |
| dissolve | Soft swell or room tone only |
| hard_cut | None (silence carries the cut) |

## Agent Usage

- **Storyboard Artist**: Sets `cut_type_intent` + `audio_sync_hint` per beat — intent, not frame-precise.
- **Editor**: Finalizes `cut_type` + `audio_sync_ref` against real Whisper timestamps. Only authority on timing.
- **Motion Designer**: Maps `cut_type` → Remotion `transition_token` + overlay. Implements, doesn't choose.
- **Sound Designer**: Tags `sfx_on_cuts[]` and `sync_markers[]` per Editor's cut list.
- **Post Supervisor**: Enforces picture lock — no timing changes after Editor signs off.
