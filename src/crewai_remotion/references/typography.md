# Typography — 9:16 Mobile-First

Text on vertical social video must be readable at arm's length on a phone screen. Every word on screen serves retention — not decoration.

## Type Hierarchy Tiers

Agents pick a tier, not a pixel size. The resolver maps tier → size per brand.

| Tier | Role | Max words | Max lines | Typical size (1080w) | Weight |
|------|------|-----------|-----------|---------------------|--------|
| display | Hook headline, stat number | 5 | 1 | 72-96px | 700-800 |
| headline | Body point title, quote | 8 | 2 | 48-64px | 600-700 |
| body | Supporting text, subhead | 15 | 3 | 28-36px | 400-500 |
| caption | Captions, labels, CTA detail | 25 | 2 | 20-24px | 400-500 |

### Tier Selection Rules

- **Hook beat**: display tier only — one big idea.
- **Body point**: headline tier for title + body tier for subhead if needed.
- **Stat reveal**: display tier for the number, body tier for context.
- **Quote**: headline tier for quote text, body tier for attribution.
- **CTA**: headline tier for action text.
- Never use display tier on consecutive beats — alternate display/headline.

## Max Words on Screen

- **Hard rule**: 8 words maximum on screen per beat for 9:16.
- Count includes headline + subhead combined.
- If a VO line is 18 words: split across beats, or show only key words on screen.
- Captions are separate — they follow VO word-for-word but don't count toward the 8-word limit.

## Contrast Requirements

- **WCAG AA minimum**: 4.5:1 contrast ratio between text and background.
- **WCAG AAA preferred**: 7:1 for display tier headlines.
- Test contrast against the actual background pixel at text position — not the global background color.
- Gradient backgrounds: measure contrast at the darkest point under text.
- Caption highlight color: must achieve 4.5:1 against surface when used as background for text.

## Weight Contrast

- Heading vs body weight difference must be ≥ 200 (e.g., 700 vs 400).
- If brand only has weights [400, 700], use 700 for display/headline, 400 for body/caption.
- Emphasis within a line: use color or scale, not weight change alone — weight shifts on single words read as rendering bugs.

## Alignment

- **Never center-align body text on 9:16.** Center alignment only for:
  - Single-line display headlines (hook only)
  - Stat numbers
  - CTA single words
- Left-align for: body points, quotes, multi-line headlines.
- Right-align for: accent text, attribution, secondary data.
- Text alignment should follow the focal zone: left zone → left-align, right zone → right-align.

## Tracking and Leading

- Display tier: tracking -1% to -2% (tight for impact).
- Headline tier: tracking 0% (default).
- Body tier: tracking +1% to +2% (breathing room at small sizes).
- Leading (line-height): 1.1× for display, 1.2× for headline, 1.4× for body.

## fitText Rules

- Always use `fitText({ withinWidth, fontFamily, fontWeight })` with a cap: `Math.min(fontSize, maxSize)`.
- `withinWidth` = frame width minus (2 × safe_margin) — text never bleeds to edge.
- Use `fillTextBox` to detect overflow before render. If text overflows: truncate, split beat, or drop to lower tier.
- **Measurement = render**: identical `fontFamily`, `fontSize`, `fontWeight`, `letterSpacing` in both `measureText` call and JSX element. Drift here causes invisible layout bugs.

## Font Loading

- Load brand fonts via `@remotion/google-fonts` or `@remotion/fonts` with explicit weights and subsets.
- Use `delayRender` until fonts are loaded — never render with fallback font.
- Pre-load only the weights used (400, 700 typically) — not the entire family.

## TikTok/Reels Caption Formatting

- Captions use body/caption tier.
- `createTikTokStyleCaptions({ combineTokensWithinMilliseconds: 800 })` groups 2-4 words.
- Highlight color (`caption_highlight`) on current word only — not full phrase.
- Caption position: bottom 15% of frame (y: ~1600-1750 at 1920h), above UI overlays.
- Captions never overlap headline zone — if conflict, captions move to lower third, headline stays.

## Agent Usage

- **Typography Director**: Primary user. Sets `tier`, `weight_contrast`, `alignment`, `max_lines`, `emphasis_words` per beat.
- **Compositor**: Receives TypeSpec; places text in assigned zones with correct alignment.
- **Caption Designer**: Formats captions with correct tier, highlight color, and position.
- **QC Script Supervisor**: Checks word count, contrast ratios, safe zone compliance.
- **Mograph TD**: Implements `fitText` with correct measurement = render; no layout overrides.
