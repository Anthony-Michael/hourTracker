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
| Interval | 60 s | Enough resolution to place a departure within a minute or two |
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

## What gets measured

Once traces arrive, the analysis answers:

- **Departure accuracy.** How close does the last-sample-inside-the-site-cluster come to
  the reported finish time? Target: within 5 minutes. Past 15 minutes the nightly
  confirm becomes a nightly correction.
- **Cluster stability.** Does the day's on-site sample cloud form a coherent, boundable
  region, and how far does it drift between days as the work zone moves along the road?
  This determines whether a learned cluster is viable or whether the corridor problem
  (§11 of the spec) is fatal.
- **False boundary crossings.** How often does the trace leave and re-enter any plausible
  site boundary during a confirmed continuous shift? Each one is a potential spurious
  "you left" event.
- **Nearby confusables.** What distinguishes the site cluster from adjacent locations a
  flagger passes through — a gas station, a yard, the road itself, which is *also* the
  work zone.
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
