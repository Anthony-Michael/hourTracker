# Hour Log — Design Specification

> Generated from a `design` consultation with `oiloil-ui-ux-guide`.
> Style family: `modern-minimal`, shifted to a **field register** — larger type, heavier
> contrast, and no decorative restraint-for-its-own-sake. The shift is driven by
> use context, not taste: this app is read outdoors, in daylight glare, one-handed.

## 1. Design direction

- **Product**: A private, passive log of hours on a job site. It infers the day from
  location and time, asks the user to confirm it once, and keeps the record so that
  when a paycheque looks light they have something to check it against. It is a
  **second record**, not a timesheet — it never submits anything anywhere.
- **Primary user**: A road flagger. Fixed 7:00 AM start, variable finish (12:30 PM to
  past 6:00 PM), works through lunch and is paid through it. Paid a minimum 8 hours
  regardless of a short day; time-and-a-half past 9 hours. Hours are submitted on his
  behalf by the employer — he never enters them, he only needs to check them.
- **Style family**: `modern-minimal` (layout, restraint, grid) with a field-instrument
  shift: display sizes go up, neutrals go high-contrast, decoration goes to zero.
- **References**: None named by the user. Direction was derived from the work context.
- **Tone**: Plain, unfussy, evidentiary. The app is a witness, not an assistant.
- **Hard constraints**:
  - Legible in direct sunlight — the governing constraint. Drives the contrast floor,
    the type sizes, and the rejection of gray-on-gray hierarchy.
  - One-handed, possibly gloved. 56px primary targets, 44px minimum for anything else.
  - Glanceable. The period total and the flagged days must read in under 3 seconds.
  - Light and dark themes both ship.
- **Locale**: primary `en-CA`. No secondary.

## 2. Color

The accent is hi-vis safety orange — the color of the vest and the cones. It is used in
exactly two places: days that ran past 9 hours, and the button that commits a record.
Nothing else earns it, so its meaning never needs a legend.

Note the split between `--color-primary` (a **fill**) and `--color-primary-ink` (**text**).
Raw hi-vis orange is 3.24:1 on the light ground — fine for a 3px stripe, unusable for
words. Any orange *text* uses the ink value.

### Brand

- `--color-primary`: `#F25C05` — fills only: the long-day stripe, the pending pill,
  the primary button. Never text.
- `--color-primary-ink`: `#9E3B00` — orange *text*: flagged hour figures, the "ran past
  9 hours" label, section eyebrows. 6.64:1 on `--color-bg`.
- `--color-primary-subtle`: `#FDEEE3` — the row wash behind a long day.
- `--color-on-primary`: `#1A1815` — ink on an orange fill. Dark-on-orange is the actual
  high-visibility convention (road signage), and it clears 5.32:1 where white-on-orange
  only manages 3.33:1.
- `--color-secondary`: N/A — a second brand color would compete with the one signal the
  accent carries.

### Neutrals (warm-biased toward the accent)

- `--color-bg`: `#FCFCFA`
- `--color-surface`: `#FFFFFF`
- `--color-border`: `#DDD8D0` — hairline rules between days
- `--color-border-strong`: `#C7C0B5` — quiet button outlines, device chrome
- `--color-text`: `#1A1815` — 17.25:1
- `--color-text-muted`: `#746B5E` — 5.10:1 on bg, 4.62:1 on the subtle wash

**There is no third text tier.** A `#A39B90` faint tone was specified and cut: it
measured 2.67:1, which fails outdoors regardless of what the guideline permits. The
hierarchy that tier was carrying is now expressed with **size and weight** instead of
lightness — an 11px mono uppercase label and 16px body can share one color and still
read as different ranks. Do not reintroduce a lighter text tone.

### Semantic

- `--color-error`: `#B3261E` — location permission revoked, tracking stopped
- `--color-success`: N/A — confirmation is expressed by the record changing state, not
  by a green tick.
- `--color-warning`: N/A — deliberately absent. A long day is not a warning; it is the
  most valuable day in the period. Coloring it as a caution would invert the meaning.
- `--color-info`: N/A.

### Dark mode

- `--color-bg`: `#171512`
- `--color-surface`: `#1E1B18`
- `--color-border`: `#2E2A26`
- `--color-border-strong`: `#423C35`
- `--color-text`: `#F2EFE9` — 15.88:1
- `--color-text-muted`: `#948C80` — 5.49:1 on bg, 4.87:1 on the subtle wash
- `--color-primary`: `#FF7A22`
- `--color-primary-ink`: `#FF9A52` — 8.67:1
- `--color-primary-subtle`: `#2E1D10`
- `--color-on-primary`: `#1A1815` — unchanged across themes
- `--color-error`: `#FF6B5E`

Every pair above was computed, not estimated. The floor is 4.5:1 for all text including
muted; re-verify on any palette change.

## 3. Typography

| Role | Font | Weights | Source |
|---|---|---|---|
| Interface | IBM Plex Sans | 400 / 500 / 600 | Google Fonts |
| Record | IBM Plex Mono | 400 / 500 / 600 | Google Fonts |

**The sans/mono split is semantic, not decorative.** Sans is the interface talking.
Mono is a recorded fact — every timestamp, every hour figure, every date. Two
consequences, both deliberate:

1. Tabular figures mean a column of fourteen days aligns on the decimal, so finding the
   odd day is a glance rather than a read. `font-variant-numeric: tabular-nums` is set
   on every numeric run.
2. Mono reads as machine record rather than opinion — which is exactly the claim the
   app is making about its own data.

Inter is not used. Plex carries technical-documentation provenance that suits a log.

### Type scale (px)

`9 / 11 / 12 / 13 / 15 / 16 / 19 / 21 / 22 / 26 / 56 / 108`

The scale is deliberately gapped rather than smooth. Small sizes cluster (9–16) because
labels and metadata need fine rank separation now that the third color tier is gone; the
display sizes (56, 108) stand far apart because they are the two numbers the app exists
to show. Nothing lives between 26 and 56.

### Body measure

- Target: 40–55 characters. This is a phone app; there is no long-form reading.
- Line-height: 1.45 for dense list metadata, 1.5 for UI body, 1.55–1.6 for the
  explanatory notes.
- Heading letter-spacing: `-0.01em` to `-0.02em`. Display figures: `-0.03em` to `-0.05em`.

## 4. Spacing

- Base unit: `4px`
- Allowed scale: `4 / 8 / 12 / 16 / 24 / 32 / 48 / 64`
- Density: `balanced` in the list, `spacious` on the confirm screen. The confirm screen
  is a single decision and should feel like one; the period screen is a dense record and
  should feel like one.
- Off-scale spacing requires a code comment justifying it. Current known exceptions:
  the 3px long-day stripe (a data mark, sized to the hairline system, not the spacing
  scale) and `vertical-align: 1px` on the pending pill (optical baseline correction).

## 5. Radius

- `--radius-sm`: `4px` — buttons, nav controls, the default for everything
- `--radius-md`: `8px` — sheets and overlays only
- `--radius-lg`: N/A — nothing in this app is large and rounded
- `--radius-full`: `9999px` — the pending pill, and nothing else

Small radii throughout. This is an instrument, not a toy; soft corners would undercut
the claim that the record is solid.

## 6. Elevation / shadow

**Flat — no shadows anywhere.** Container strategy is `divider` (§7a); separation comes
from hairlines and spacing. This includes overlays: a sheet separates itself with a
strong top border and a scrim, not a drop shadow.

- `--shadow-sm` / `--shadow-md` / `--shadow-lg`: N/A — not defined, deliberately, so
  they cannot be reached for.

## 7. Motion

- Vocabulary: `minimal`
- Default duration: `100ms` for micro (press, focus), `150ms` for state change,
  `200ms` for the confirm sheet entering
- Easing: `ease-out` for entrances, `ease` for state changes
- Allowed: opacity fade, short translate (≤8px), the sheet's vertical slide
- Forbidden: bounce, spring, parallax, number count-up animation, any celebratory
  motion on confirm. Confirming a day is bookkeeping, not an achievement — animating it
  would make a serious record feel like a game.
- Respect `prefers-reduced-motion: reduce` by dropping to opacity-only.

## 7a. Container strategy

- **Strategy**: `divider`

A log book is ruled lines. Fourteen floating cards would fragment the one thing the
period screen is for: running your eye down a single column of hours without
interruption. Sections separate with `border-bottom: 1px solid var(--color-border)`;
nothing is enclosed in a box.

- **Per-surface overrides**:
  - Period list: `divider` — hairline between each day row
  - Confirm screen: `divider` — the start/end block is bounded by a top and bottom rule
  - Adjust screen: `divider` — each candidate time is a full-bleed row with a rule
  - Settings: `divider`
- **Implementation notes**: The long-day row is the one place a background fill appears
  (`--color-primary-subtle`), and that fill is *data*, not a container. It marks the row
  as belonging to a category; it does not group its contents. Do not extend the pattern
  to non-semantic grouping.

## 7b. Icon system

- **Set**: `phosphor`
- **Weight**: `bold` — matches the heavier field register; regular weight disappears
  in glare
- **Treatment**: `monochrome`, `currentColor`
- **Sizes**: `15 / 19 / 20 px` in use; `32 / 48 px` reserved for empty states
- **Mixing**: no second set. If Phosphor lacks an icon, use the closest match or use a
  word instead — this app is comfortable with words.
- Icons never appear alone on a control that performs an action. The only icon-only
  controls are the period back/forward chevrons, which are universally understood and
  carry `aria-label`.

## 7c. Decoration

| Surface | Gradients | Textures | Motifs |
|---|---|---|---|
| Period list | `none` | `none` | `none` |
| Confirm | `none` | `none` | `none` |
| Adjust | `none` | `none` | `none` |
| Settings | `none` | `none` | `none` |

Zero decoration, everywhere, deliberately. The one graphic element in the app — the
3px orange stripe on a long day — is a data mark. If a gradient or texture is ever
added, the stripe stops reading as information and starts reading as styling.

## 8. Component conventions

### Buttons

- **Primary**: `background: var(--color-primary)`, `color: var(--color-on-primary)`,
  height `56px`, radius `4px`, 17px/600, icon 19px, full width.
  One per screen, maximum. It always commits a record.
- **Quiet**: transparent background, `1px solid var(--color-border-strong)`,
  `color: var(--color-text)`, same 56px height. Used for the escape hatch
  ("That's not right").
- **Nav**: 32px square, `1px solid var(--color-border)`, icon only, `aria-label` required.
- **Destructive**: N/A — nothing in this app destroys data. Deleting a day is not
  offered; a day can only be corrected, and corrections keep the original detection
  underneath.
- Minimum target 44px for any control; 56px for the primary.

### Inputs

The app is almost input-free by design — the whole point is not typing. The only true
input is the manual time picker behind "Other" on the adjust screen.

- Default: `1px solid var(--color-border)`, 4px radius, 16px text minimum (never smaller
  — iOS zooms on focus below 16px)
- Focus: `2px solid var(--color-primary)` outline with `2px` offset, always visible,
  never removed
- Error: `1px solid var(--color-error)` plus a message stating what is wrong and what to
  do about it
- Disabled: not used — hide unavailable controls rather than greying them, since grey
  disabled text cannot meet the contrast floor

### Rows (the dominant component)

The day row and the choice row are the two workhorses.

- Day row: `grid-template-columns: 62px 1fr auto` — date, span, hours. Baseline-aligned
  so the mono figures sit on one line.
- Choice row: fixed-width time column so candidate times align vertically, then a
  two-line label (what it is / where it came from).
- Both are full-bleed to the screen edges with 24px internal padding. Rules run the
  full width; there are no inset dividers.

### Cards

Not used. See §7a. If a future surface seems to need one, it probably needs a divider
and more spacing.

### Provenance labels

Every displayed time states its source in an 11px mono suffix: `scheduled`, `detected`,
`on site 6:47a`, `tap to change`. This is a **hard requirement, not a nicety**. A number
the app inferred and a number the user confirmed are different kinds of fact, and the
app must never blur them — least of all on the day that ends up being disputed.

## 9. Surfaces

- **Period list** (primary, opened when a stub looks wrong): sticky header carrying the
  period range, the total in 56px mono, and a one-line meta ("11 days worked · 3 past 9
  hrs"). Below, one row per calendar day including non-work days, which render as
  "No site time" rather than being omitted — a missing row is indistinguishable from a
  bug, and an empty day is real information.
- **Confirm** (the daily touchpoint): a single decision, full screen, no navigation. The
  reason it is asking appears *first*, at the top, in orange ("Ran past 9 hours"). The
  figure is 108px. Two actions, stacked, primary on top.
- **Adjust** (the correction path): candidate times the app actually observed, listed
  largest-affordance-first, with the manual picker last. The recomputed total updates
  above the save button so the consequence of the choice is visible before committing.
- **Settings**: scheduled start time, pay-period boundaries, the long-day threshold
  (default 9), notification timing. Divider-separated rows, no cards.
- **Marketing landing**: N/A — this is a personal tool with one user.

## 10. Anti-patterns for this project

- **No dollar amounts, ever.** The app reports hours. The moment it multiplies by a rate
  it is asserting what you are owed, and a confidently wrong number is worse than no
  number — it is the exact failure the app exists to catch.
- **No third text tier.** See §2. Any color lighter than `--color-text-muted` fails in
  daylight.
- **No green success states or celebratory motion on confirm.** Bookkeeping, not a streak.
- **No cards, no shadows.** See §7a.
- **No icon-only action buttons** apart from the period chevrons.
- **Never treat a detected time as a confirmed one.** If provenance is unknown, say so;
  do not round it into certainty.
- **Never present arrival time as start time.** They are different clocks (§11).
- **No progress rings, no daily goal, no streaks.** Working more hours is not an
  achievement to be gamified — it is a fact to be recorded accurately.

## 11. Open questions

- ~~**Geofencing a corridor, not a point.**~~ **Resolved — the approach changed.**
  Geofencing was abandoned before implementation. It required knowing where the site
  is, which is the one thing that cannot be relied on: a flagging site shifts along the
  road day to day and the parking spot varies. The replacement detects the *transition
  out of driving* instead, bracketing the day between the morning and evening commutes
  (`analysis/segment.py`). It needs no learned site, works on day one at a site never
  visited before, and tolerates the phone riding in the truck or in a pocket. Confirmed
  with the user: the truck is parked in the morning and does not move until he leaves,
  and he is on foot at his post all day — so within a work day, driving is never work.
  Sustained road speed mid-shift would break this, and does not occur for this user.
- **Battery and sampling rate.** Passive tracking across a 10-hour outdoor day, on a
  phone in a pocket, is the main technical risk to the product being usable at all.
  Not yet investigated.
- **The 9-hour threshold's exact basis.** Whether the employer counts the 9 hours from
  the clock or excludes anything, and whether it shifts on weekends, is unconfirmed.
  The app currently uses it only to decide *when to ask*, never to compute pay, which
  keeps the consequence of being wrong small. Do not deepen this dependency without
  confirming the rule.
- **Multiple sites in one day.** Not yet designed. A flagger moved between two jobs mid-
  shift would currently read as one continuous day, which may be correct for pay but
  loses information.
- **Export.** No export exists. If the log is ever used in an actual pay dispute, a
  plain-text or PDF export carrying the provenance labels would matter more than
  anything on screen.
