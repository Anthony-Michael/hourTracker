# Field Test 01 — Can location recover a work day?

**Status**: awaiting data
**Blocks**: all application development

## Why this comes first

The entire design in `../design-spec.md` rests on one unverified assumption: that a
phone's location trace is sufficient to infer a flagger's start and finish times without
manual input. Everything downstream — the nightly confirm, the long-day flag, the whole
premise of a passive record — is worthless if that inference is unreliable.

An app that guesses wrong most nights is worse than the notebook it replaces, because it
costs the same attention and adds false confidence.

This test answers the question with an off-the-shelf GPS logger and two days of real
work, before any code is written.

## Method

The user records his normal working day with an existing open-source GPX logger, and
separately writes down what actually happened. Neither the app nor the analysis is ours;
the only thing being tested is whether the resulting trace supports the inference.

**Logger**: GPSLogger by Mendhak (Android). Free, open source, local-only.

**Required settings** — the one place this test can be silently ruined:

| Setting | Value | Why |
|---|---|---|
| Interval | 10 s | The commute is only 5-10 minutes. At 60 s that is roughly five samples for the entire trip, and the trip is what the whole method depends on |
| Distance filter | 0 | **Critical.** Movement-triggered logging discards stationary samples, and standing still on site is the signal we most need |
| Format | GPX | Standard, parseable |
| Permission | Always | "While using" stops sampling on lock, which is the normal state of a phone in a pocket |
| Battery saver | Off | We want the honest battery cost, not an optimised one |

**Ground truth** — recorded in the moment, not from memory:

1. Actual start time
2. Actual finish time
3. Battery percentage at start and at end
4. Anything unusual (setup moved, left and returned, different site, phone died)

Without (1) and (2) the trace is unfalsifiable and the day is wasted.

**Sample**: 2–3 days. At least one day past 9 hours is worth more than several ordinary
days — long days are where precision has monetary consequence and where the inference
must hold.

## The inference being tested

`../analysis/segment.py`, which brackets the day between commutes rather than fencing
the site:

```
1.  speed between consecutive points
2.  rolling median over ~90s       -- window sized in SECONDS, not samples
3.  above 4.5 m/s = driving        -- threefold margin over walking (1.4 m/s)
4.  a drive brackets the day only if it lasts >= 90 s AND covers >= 1 km
5.  work day = end of first qualifying drive -> start of last
```

Step 4 is load-bearing: repositioning a truck a few hundred metres can briefly exceed
the speed threshold, and without the displacement filter one long day would be split
into two short ones.

Step 3's threshold started at 8 m/s, reasoned from open-road driving, and that was a
real bug. The commute being tested is 5-10 minutes through town; a 2.2 km version of it
averages 7.3 m/s and never sustains 8, so the segmenter found zero qualifying drives and
could not bracket the day at all. The margin that matters is against walking, not
against highway speed, so 4.5 m/s keeps a threefold gap over a walking pace while still
catching a slow commute.

**Confirmed with the user**: the truck is parked on arrival and does not move until he
leaves, and he is on foot at his post all day. Within a work day, driving is never work.
Sustained road speed mid-shift — a pilot car, or moving between sites — would break the
bracket, and does not apply here.

Step 2's window is sized in seconds rather than samples for the same reason: a fixed
5-sample window is 50 s of smoothing at a 10 s interval but a full 5 minutes at 60 s, and
five minutes of smoothing applied to a six-minute commute would erase it silently.

`../analysis/test_segment.py` passes nine synthetic days built from stated ground truth,
including both a fast and a slow short commute at two logging intervals, an overtime day,
a mid-shift truck move, walking off site to a porta potty, and a trace whose logger was
started after arrival. Synthetic GPS is far cleaner than real GPS, so that result proves
the logic and nothing else. This field test is the actual verdict.

## What gets measured

- **Departure accuracy.** How close is the inferred finish to the reported one? Target
  within 5 minutes. Past 15 the nightly confirm becomes a nightly correction.
- **Deceleration sharpness.** How cleanly does the morning commute resolve into a stop?
  This is the entire mechanism — if arrival is smeared across ten minutes of slow
  traffic near the site, the bracket loosens.
- **Spurious qualifying drives.** Anything inside the window that clears both the
  duration and displacement filters. Each one would split a real day in two.
- **Site spread.** Radius of gyration across the window. Not needed for detection any
  more, but it tells us whether a site could be *labelled* day to day ("same site as
  yesterday") and bounds how far the work zone actually creeps.
- **Signal quality.** Sample gaps, reported accuracy radius, dropouts.
- **Battery cost.** Percentage drop across a full shift, which decides whether all-day
  passive tracking is viable at all.

## Outcomes and what each one means

| Result | Consequence |
|---|---|
| Departure recoverable within ~5 min | Premise holds. Build the app as designed. |
| Recoverable but noisy | Premise holds with work — smoothing, dwell-time thresholds, or a differently shaped boundary. Spec §11 gets answered rather than removed. |
| Not recoverable | Passive inference cannot carry the product. Redesign around a lighter touch — a single end-of-day prompt, or a widget — rather than shipping something that nags nightly. |

The third outcome is a success for this test. Learning it now costs two days of a
logger app; learning it after building costs the project.

## Platform

**Android**, confirmed. This resolves what was the largest open risk to the product
being buildable at all:

- Background location is permissive enough for continuous sampling, given a foreground
  service and `ACCESS_BACKGROUND_LOCATION`. The equivalent on iOS is far more
  constrained and might have forced a redesign regardless of what this test finds.
- Distribution is a sideloaded APK — no store review, no developer account, no annual
  fee. For a single-user personal tool this is the difference between shipping and not.

Two Android-specific risks move into scope and should be watched during this test, since
the logger app faces exactly the same constraints the real app will:

- **Battery optimisation.** Aggressive OEM power management (Samsung, Xiaomi and others
  are notably worse than stock Android) can suspend a background service regardless of
  permissions. Gaps in the recorded trace are the symptom to look for.
- **Foreground service notification.** Continuous location requires a persistent
  notification. It cannot be hidden, so it becomes part of the product's daily presence
  whether we want it or not.
