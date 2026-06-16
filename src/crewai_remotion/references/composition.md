# Composition — 1080×1920 Vertical Frame

Mobile-first composition for 9:16 social video. Every beat has exactly one focal point. Nothing centers by default. Negative space is intentional, not empty.

## Rule of Thirds (9:16 Grid)

```
┌─────────┬─────────┬─────────┐
│  TL     │  TC     │  TR     │   ← Top third (hook zone)
│         │         │         │
├─────────┼─────────┼─────────┤
│  ML     │  MC     │  MR     │   ← Middle third (body zone)
│         │         │         │
├─────────┼─────────┼─────────┤
│  BL     │  BC     │  BR     │   ← Bottom third (CTA zone)
│         │         │         │
└─────────┴─────────┴─────────┘
```

Grid intersections (TL, TR, ML, MR, BL, BR) are power points — place focal elements here.

### Zone Assignments by Beat Type

| Beat type | Headline zone | Illustration zone | Background emphasis |
|-----------|--------------|-------------------|-------------------|
| Hook | TC or TR | TL or BR | Full primary |
| Body point | ML or MR | Opposite third | Secondary gradient |
| Stat | MC (centered, exception) | None or subtle | Accent burst |
| Quote | ML with portrait inset | TR | Muted surface |
| CTA | BC | None | Primary fade to surface |

## Focal Point

- **One focal point per beat.** The viewer's eye should land exactly where you intend.
- Focal hierarchy: headline text > illustration > accent shape > background detail.
- If a beat has a headline AND an illustration, one is dominant (80% visual weight), the other is supporting (20%).
- Change focal zone between consecutive beats — never two beats with headline in same grid zone.
- Hook: focal in top third. CTA: focal in center or bottom third.

## Visual Weight

Elements compete for attention. Balance deliberately.

- **Heavy**: Large text, bright color, high contrast, motion, human face.
- **Light**: Small text, muted color, low contrast, static, geometric shapes.
- Distribute weight diagonally: heavy top-right → light bottom-left; or heavy mid-left → light bottom-right.
- Never equal weight on both sides of center = AI slop symmetry.

## Negative Space

- **Minimum 25% negative space per frame** for `text_density: minimal` brands.
- Hook beats: 40% negative space minimum — let the hook breathe.
- Body beats: 25-30% negative space.
- CTA: 35% negative space — focus on the action.
- Negative space is the background, not empty void. Texture, subtle gradient, depth layers fill it without competing.

## Eye Path (9:16 Scrolling)

Vertical eye path flows top-to-bottom, matching scroll direction:

1. **0-1s**: Top third — hook text or visual shock. Viewer hasn't scrolled yet.
2. **1-3s**: Middle third — hook payoff. Viewer is reading.
3. **3-8s**: Middle third moving down — body content.
4. **8-15s**: Alternating middle zones — re-hook or pattern interrupt.
5. **15-25s**: Lower middle — proof/value.
6. **25-30s**: Bottom third — CTA.

Lead the eye with motion direction: enter from bottom → viewer scrolls up. Enter from top → viewer reads down.

## Depth Layers

Every beat has at least two depth layers:

1. **Background** (deepest): Mesh gradient or solid with texture. Never competes for attention.
2. **Content** (mid): Headline, illustration, data. The focal point lives here.
3. **Foreground** (closest, optional): Brand mark, caption overlay, subtle vignette.

Depth is created by: color saturation (background desaturated), scale difference, motion parallax (background moves slower).

## Safe Zones

- **Edge margin**: 48px minimum from all edges (TikTok/Reels UI overlays).
- **Bottom danger zone**: Bottom 250px is covered by engagement buttons, captions, username on most platforms.
- **Right danger zone**: Right 120px is covered by like/comment/share buttons.
- **Top safe zone**: Top 120px is usually clear but keep below status bar area.
- Headline text: never in bottom 250px or right 120px.
- CTA: keep within center 60% of frame (x: 216–864 at 1080w).
- Captions: bottom 150px (above UI but below content).

## Agent Usage

- **Compositor**: Primary user. Sets `focal_point`, `headline_zone`, `illustration_zone`, `negative_space_ratio`, `balance_notes`, `safe_margin_ok` per beat.
- **Storyboard Artist**: Plans eye path across beats — which zone each beat's focal lives in.
- **Production Designer**: Sets background depth layers and atmosphere per beat.
- **Caption Designer**: Places captions respecting safe zones and headline zone.
- **QC Script Supervisor**: Checks zones don't violate safe margins.
