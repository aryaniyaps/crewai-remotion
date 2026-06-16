# Vertical Layout — 1080×1920 Platform Safe Zones

Layout for TikTok, Reels, Shorts. Platform UI elements occupy fixed screen regions — content must work around them, not under them.

## Safe Zone Map (1080×1920)

```
┌──────────────────────────────────┐  0px
│  Top safe: 0-120px               │  ← Status bar / nav (usually clear)
│  (use for headline only)         │
├──────────────────────────────────┤  120px
│                                  │
│  Content safe: 120-1670px        │  ← PRIMARY CONTENT ZONE
│  (all critical content here)     │     1440px tall
│                                  │
├──────────────────────────────────┤  1670px
│  Bottom danger: 1670-1920px       │  ← UI overlays
│  250px — DO NOT place:           │     • Username (@handle)
│  • Headlines, CTA text           │     • Caption text
│  • Critical visuals              │     • Like/Comment/Share
│  • Stat numbers                  │     • Music disc
│  Only: subtle brand mark OK      │     • Follow button
└──────────────────────────────────┘  1920px
```

## Danger Zones (Absolute No-Go for Content)

### Bottom 250px (y: 1670–1920)
Overlapped by: username, caption, like/comment/share buttons, music disc, follow button.
- **Never**: headlines, CTA text, stat numbers, illustration focal points.
- **Allowed**: subtle brand logo (small, low opacity), background only.

### Right 120px (x: 960–1080)
Overlapped by: like button, comment button, share button, bookmark.
- **Never**: end of headline text, CTA text edge, illustration focal point.
- **Allowed**: background gradient bleed, texture.

### Top 120px (x: 0–1080, y: 0–120)
Usually clear but keep safe: status bar, navigation hints.
- **Avoid**: small text, detail elements.
- **Allowed**: headline top edge (display tier is large enough to read through partial obstruction).

## Headline Placement Tiers

| Tier | Y position (center) | Best for |
|------|---------------------|----------|
| top_third | 360px | Hook headlines — first thing viewer sees |
| upper_mid | 720px | Body point titles |
| mid_center | 960px | Stat numbers (exception: centered) |
| lower_mid | 1200px | Quote text, proof points |
| bottom_safe | 1520px | CTA text (as low as safe) |

Headline x-position follows compositional zone (left third: x=360, right third: x=720) — never center unless stat number or single-word CTA.

## Illustration Placement Zones

```
┌──────────────────────────────────┐
│  TL zone     │  TR zone          │   ← Top corners: hook illustrations
│  (x:48-360)  │  (x:720-1032)     │
│  (y:120-480) │  (y:120-480)      │
├──────────────┼──────────────────┤
│  ML zone     │  MR zone          │   ← Mid corners: body illustrations
│  (x:48-360)  │  (x:720-1032)     │
│  (y:600-1200)│  (y:600-1200)     │
├──────────────┼──────────────────┤
│  BL zone     │  BR zone          │   ← Bottom corners: subtle only
│  (x:48-360)  │  (x:720-1032)     │      (danger zone overlap)
│  (y:1320-1670│  (y:1320-1670)    │
└──────────────┴──────────────────┘
```

Illustration scale tiers: `sm` (120-180px), `md` (200-280px), `lg` (320-400px).

## Zone Collision Rules

- **Headline + Illustration**: Must be in different zones. If headline in TR, illustration in ML or BL.
- **Headline + Captions**: Captions move to bottom 15% (y: 1600-1750), headline stays in content zone.
- **Illustration + Captions**: No overlap. If illustration in BR, captions shift to center-bottom.
- **Logo + Headline**: Logo in opposite corner from headline. If headline TR, logo in TL or BL.

## Layout Variants (Agent Picks, Not Pixels)

| Layout | Description | When to use |
|--------|-------------|-------------|
| left_stack | Headline left, illustration right | Body points, quotes |
| right_stack | Headline right, illustration left | Alternating body beats |
| center_focus | Single element centered | Stat numbers, single-word CTA |
| top_down | Headline top, illustration below | Hook beats, explainers |
| diagonal_tl_br | Headline TL, accent BR | Energy beats, transitions |
| diagonal_tr_bl | Headline TR, accent BL | Pattern interrupts |

Alternate layout between consecutive beats — never `left_stack` twice in a row.

## Thumb-Zone Captions

On mobile, captions are read in the lower portion of the screen:
- Caption y-position: 1600-1750px (above danger zone, below content).
- Caption font size: 20-24px (body tier) — readable at arm's length.
- Caption max width: 900px (leaving 90px margins on each side).
- If a beat has both headline and captions: headline in top/mid zone, captions in bottom zone — clear separation.

## Agent Usage

- **Compositor**: Primary user. Sets `headline_zone`, `illustration_zone`, `logo_zone`, `safe_margin_ok` per beat. Checks all zone collision rules.
- **Typography Director**: Selects headline placement tier per beat.
- **Illustrator**: Selects illustration zone per beat (never same zone as headline).
- **Caption Designer**: Places captions in thumb zone, avoiding headline/illustration zones.
- **QC Script Supervisor**: Validates no element in danger zones, no zone collisions.
