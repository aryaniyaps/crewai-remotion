# Sound Design — TikTok/Reels Cut-Driven SFX

Vertical short-form audio is cut-first, music-second. SFX serve transitions and reveals — never background noise. Every sound effect has a cut to justify it.

## Principles

1. **Cuts drive SFX, not the other way around.** SFX bridges reinforce the Editor's cut types — they don't create rhythm on their own.
2. **Whoosh transitions are the backbone.** Slides, wipes, cross-cuts, and montage sequences all benefit from short whoosh bridges. Keep them tight: 4-8 frames, ducked under VO.
3. **Impact on reveals.** Smash cuts and stat reveals get impact/hit SFX hard-synced to the cut frame. Optional: 2-4 frame silence gap before the hit for anticipation.
4. **Subtle ambient layers only when motivated.** A soft rise under a hook buildup is valid. Ambient texture on every beat is noise — short-form audiences tune it out.
5. **Silence is a design tool.** J-cuts, L-cuts, dissolves, and invisible cuts carry their own audio rhythm — stacking SFX on top destroys the edit.
6. **VO is primary.** SFX must not obscure words. Duck or place SFX in VO pauses, or at beat boundaries where VO is naturally quiet.

## Available SFX Catalog

| SFX ID | Duration | Tags | Character |
|--------|----------|------|-----------|
| `whoosh` | 400ms | transition, fast | Short aggressive whoosh — jump cuts, cross cuts |
| `whoosh_low` | 800ms | transition, slow | Deeper, slower whoosh — match cuts, montage bridges |
| `swoosh` | 600ms | transition, smooth | Smooth sweeping transition — cut_on_action |
| `impact` | 500ms | emphasis, cut | Heavy impact hit — smash cuts, reveals |
| `hit` | 350ms | impact, heavy | Hard percussive hit — accent on stat reveals |
| `pop` | 200ms | emphasis, light | Light pop — text appearance, minor accents |
| `click` | 100ms | ui, light | Subtle click — UI element reveal, cursor sync |
| `rise` | 1200ms | buildup, tension | Rising tension swell — hook buildup, pre-reveal |

## SFX-to-Cut Mapping (SFX_BRIDGE)

| Cut Type | SFX | Rationale |
|----------|-----|-----------|
| `hard_cut` | _none_ | Silence carries the cut — rhythm alone is enough |
| `jump_cut` | `whoosh` | Short aggressive whoosh reinforces the temporal jump |
| `match_cut` | `whoosh_low` | Deep sweep bridges the matched elements |
| `smash_cut` | `impact` | Impact hit hard-synced to cut frame; may add `whoosh` preceding as second SFX |
| `cut_on_action` | `swoosh` | Smooth sweep follows the action motion |
| `j_cut` | _none_ | Audio already leads — SFX would clash with VO pre-lap |
| `l_cut` | _none_ | Audio already trails — SFX would clutter the emotional carry |
| `cross_cut` | `whoosh` | Quick whoosh marks the parallel-action switch |
| `montage` | `whoosh_low` | Subtle whoosh every 2-3 items (not every item) |
| `dissolve` | _none_ | Fade carries its own weight — SFX makes it heavy |
| `invisible_cut` | _none_ | By definition invisible — any SFX breaks the illusion |

## Constraints

- **Max 1 SFX cue per beat** — each beat is 2-4 seconds; more than one SFX in that window is clutter.
- **Exception: `smash_cut` may use 2 SFX** — a `whoosh` (or `rise`) leading into the `impact` for a bigger payoff. Place the whoosh 6-12 frames before the impact.
- **No SFX on `dissolve` or `invisible_cut`** — these transitions are designed to be seamless; SFX violates their intent.
- **No SFX on `j_cut` or `l_cut`** — split edits already carry audio across the cut boundary.
- **`montage` SFX every 2-3 items, not every item** — micro-whooshes on every beat in a 5-beat montage sound amateur.
- **SFX volume: 0.5-0.8** — never full-scale. Music and VO are primary; SFX is reinforcement.
- **No SFX during VO emphasis words** — duck or delay. If VO has an emphasis word at frame 120, place SFX at frame 115 or 128.

## Output Format

SoundPlan.sfx_cues[] — each entry is an `SfxCue` with:
- `frame`: exact frame number in the composition
- `sfx_id`: one of the 8 catalog IDs above
- `volume`: 0.5-0.8
- `cut_type`: which cut this SFX accompanies (from the Editor's cut_type field)
- `notes`: brief justification (e.g. "whoosh on jump_cut at hook boundary")
