# Color — Brand Role Application for Video

Color in motion graphics carries emotion, hierarchy, and brand recognition. Every beat has a color intention — not just "looks nice."

## Brand Color Roles

Each brand color has a specific job in the video frame. Never use a color outside its role.

| Brand token | Role | Where | Max coverage |
|------------|------|-------|-------------|
| primary | Hero accent, hook background, emphasis | Hook beats, CTA, stat numbers | 40% of frame |
| secondary | Body beats, depth layers, transitions | Value beats, background depth | 60% of frame |
| accent | Highlights, pattern interrupts, stat bursts | Stats, re-hooks, emphasis words | 10% of frame |
| surface | Base background, negative space, text backplate | All beats (deepest layer) | 100% of frame |
| caption_highlight | Karaoke caption emphasis only | Current word in captions | N/A (text color) |

## 60-30-10 Rule (Adapted for Video)

Per beat, color distribution:
- **60%** dominant color (surface or secondary — sets the mood)
- **30%** secondary color (primary or secondary — the content zone)
- **10%** accent (accent only — draws the eye, never overwhelms)

Hook beats: invert to 40% primary, 50% surface, 10% accent — hooks are visually aggressive.

## Per-Beat Color Intent

| Beat type | Background | Text | Accent use |
|-----------|-----------|------|------------|
| Hook | primary gradient → surface | white or surface | None (background is the accent) |
| Body point 1 | secondary solid | primary or white | Subtle shape in opposite corner |
| Body point 2 | surface → secondary gradient | primary | Accent line or dot |
| Stat | surface with accent burst | primary or white | Radial burst behind number |
| Quote | muted surface | primary | None (let text carry) |
| CTA | primary → surface gradient | white | None (action is the focus) |

## WCAG Contrast on Video

- Text on video backgrounds MUST achieve 4.5:1 contrast ratio.
- Gradient backgrounds: measure contrast at the pixel where text sits — not the edge.
- `caption_highlight` (#39E508 bright green) on `surface` (#0F0F14 near-black): 12:1 ratio — safe.
- `primary` (#FF3366 hot pink) on `surface`: ~5.5:1 — passable for large text, insufficient for body.
- If primary fails contrast on surface for body text: use white (#FFFFFF) instead, which achieves 18:1.
- Test every text-on-background combination. Agent must declare contrast tier: `high` (≥7:1), `aa` (≥4.5:1), or `fail`.

## Color Progression Across Beats

Don't use the same palette distribution for every beat — it reads as template:

1. **Hook**: Boldest color statement. Primary dominant.
2. **Body 1**: Shift to secondary-dominant. Primary as accent only.
3. **Body 2**: Surface-dominant with accent burst.
4. **Body 3**: Return to secondary-dominant (different gradient direction).
5. **CTA**: Primary returns for closure. Visual bookend with hook.

Progression creates narrative arc through color alone.

## Background Gradient Rules

- Mesh gradients: blend 2-3 brand colors with noise texture.
- Gradient direction carries meaning:
  - Top→bottom: reading flow, natural scroll.
  - Bottom→top: energy rising, build-up (use before CTA).
  - Diagonal (TL→BR): dynamic, modern.
  - Radial from center: focus, stat emphasis.
- Never use linear-gradient with 2 arbitrary colors — always from brand palette.
- Gradient stops: surface at edges, secondary/primary in focal zone — guides eye to content.

## Accent Sparingly

- Accent color covers ≤10% of frame per beat.
- Accent shapes: small circles, thin lines, dot patterns — never solid blocks.
- Accent pulses on: stat numbers, emphasis words, hook payoff, CTA button.
- Accent is the spice, not the meal. If you notice the accent color, it's too much.

## Colorist's Per-Beat Adjustments

ColorGrade (from Colorist agent) per beat:
- `bg_saturation`: 0.0 (muted) to 1.0 (full). Body beats: 0.6-0.8. Hook: 1.0. CTA: 0.8.
- `accent_boost`: 0.0 (none) to 1.0 (full). Stats: 1.0. Body: 0.2-0.4.
- `text_contrast_tier`: "high" | "aa" | "fail" — never emit "fail".

## Agent Usage

- **Art Director**: Sets overall color direction in StyleBible.
- **Colorist**: Per-beat `ColorGrade` with saturation, accent boost, contrast tier. Uses this reference.
- **Production Designer**: Background gradient direction and color distribution.
- **Compositor**: Verifies contrast ratios at text positions.
- **Brand Guardian**: Adversarial check — any color outside brand palette is a violation.
