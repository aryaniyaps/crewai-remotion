# Motion Intent — When to Move, When to Hold

Motion in social video is retention mechanics, not decoration. Every animation has a job: guide attention, signal importance, or create energy. Movement without intent is noise.

## Motion Style Presets

Brand YAML `motion_style` maps to spring presets. Agents pick the preset; code implements the springs.

| Style | Damping | Stiffness | Mass | Feel | Use case |
|-------|---------|-----------|------|------|----------|
| snappy | 20 | 200 | 0.8 | Punchy, quick, social-native | TikTok/Reels, tech brands, fast-paced |
| smooth | 30 | 120 | 1.2 | Calm, premium, deliberate | Educational, luxury, B2B |
| kinetic | 12 | 170 | 0.6 | Bouncy, energetic, playful | Entertainment, D2C, youth brands |

## Hold vs Move Decisions

For each element on screen, decide: hold, enter, exit, or subtle drift.

| Element | Hook | Body point | Stat | CTA |
|---------|------|-----------|------|-----|
| Headline | Enter up (fast) | Hold (readable) | Scale burst (spring) | Hold (locked) |
| Subhead | Enter after delay | Hold | Fade in (subtle) | — |
| Illustration | Enter from side | Subtle drift (2-4px) | Scale pulse | Fade out |
| Accent shape | Enter with overshoot | Hold | Pulse on stat | Exit |
| Background | Subtle gradient shift | Hold | Radial pulse | Fade to surface |

## Stagger Principles

Elements enter in sequence, not all at once:

1. **Background**: Frame 0 (immediate, sets the scene).
2. **Headline**: Frame 6-10 (after background settles).
3. **Illustration/Accent**: Frame 12-18 (after headline is readable).
4. **Subhead**: Frame 18-24 (supporting info last).

Stagger via `spring({ delay: i * 3 })` per element — not hardcoded frame numbers. Stagger rhythm: 3-5 frames between elements for snappy, 5-8 for smooth, 2-4 for kinetic.

## Duration by Element Type

| Element | Entry duration | Exit duration |
|---------|---------------|---------------|
| Headline (display) | 12-18 frames | 8-12 frames |
| Headline (headline tier) | 10-14 frames | 6-10 frames |
| Illustration | 14-20 frames | 10-14 frames |
| Accent shape | 8-12 frames | 6-8 frames |
| Background change | 20-30 frames | 20-30 frames |

## Composed Progress Pattern

One normalized progress value (0→1) drives opacity, translate, and scale together:

```ts
const progress = interpolate(
  frame,
  [entryStart, entryStart + entryDuration],
  [0, 1],
  { extrapolateRight: 'clamp' }
);
const opacity = interpolate(progress, [0, 0.3, 1], [0, 0, 1]);
const translateY = interpolate(progress, [0, 1], [40, 0]);
const scale = interpolate(progress, [0, 1], [0.92, 1]);
```

This prevents elements animating out of sync — the hallmark of amateur motion.

## When NOT to Animate

- **Don't animate background** on body beats — save motion for transitions.
- **Don't animate captions** — they follow Whisper word timestamps, not spring curves.
- **Don't animate every beat** — hold beats create reading time. ~40% of beats should be holds.
- **Don't animate out if transitioning to same layout** — hard_cut with no exit animation.
- **Don't animate elements that aren't focal** — supporting elements fade, don't bounce.

## Motion Intensity Caps

From ComplexityBudget:

| Intensity | Max motion layers | Max stagger depth | Entry style |
|-----------|------------------|-------------------|-------------|
| low | 2 | 2 elements | fade_in only |
| medium | 3 | 3 elements | enter_up, fade_in |
| high | 4 | 4 elements | enter_up, scale_burst, slide_in |

## Cut-on-Action Motion

When Editor specifies `cut_on_action_frame`, Motion Designer sets peak velocity at that frame:

```ts
// Peak velocity at ~70% of exit animation
const exitProgress = interpolate(frame, [exitStart, exitEnd], [0, 1]);
const velocity = spring({
  frame: exitProgress * 10,
  config: { damping: 20, stiffness: 200 }
});
// cut_on_action_frame = exitStart + exitDuration * 0.7
```

## Bezier Easing

- Entrances: `Easing.bezier(0.22, 1, 0.36, 1)` — gentle overshoot, natural settle.
- Exits: `Easing.in(Easing.cubic)` — accelerate out, no linger.
- Holds: `Easing.linear` — or no animation at all.
- Never use `Easing.out(Easing.cubic)` for entrances — it reads as lag.

## CameraMotionBlur

- Apply `CameraMotionBlur` on kinetic-style beats with fast-moving elements.
- `shutterAngle: 180` (standard film blur).
- `samples: 3` (quality/performance balance).
- disable for: static text beats, captions, fine detail elements.

## Text Animation Rules

- Never animate individual characters (typewriter effect) — reads as dated.
- Animate full text blocks: enter as unit, hold as unit, exit as unit.
- Stagger lines (not words) for multi-line text: `spring({ delay: lineIndex * 4 })`.
- Emphasis words: scale pop (1.0 → 1.08 → 1.0) over 6 frames, not color change.

## Agent Usage

- **Motion Designer**: Primary user. Sets `animation_token`, `transition_token`, `stagger_ms`, `cut_on_action_frame` per beat. Applies motion_intent.md rules.
- **Storyboard Artist**: Sets `motion_intent` (enter_up, fade_in, scale_burst) per beat — intent only, not timing.
- **Editor**: Specifies `cut_on_action_frame` in EditDecisionList.
- **Mograph TD**: Implements composed progress, springs, CameraMotionBlur per MotionPlan.
- **QC**: Checks motion intensity vs ComplexityBudget; flags jank or CSS animations.
