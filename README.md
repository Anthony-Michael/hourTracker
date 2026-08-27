# Hour Log

A passive record of hours on a job site.

It infers the working day from location and time, asks you to confirm it once in the
evening, and keeps the record. When a paycheque looks light, you have something of your
own to check it against.

## What it is not

It is not a timesheet. It does not submit hours anywhere, it does not talk to an
employer's system, and it never computes pay. Hours are already submitted for you; this
exists so that number has something to be compared against.

It also never shows dollar amounts. It reports what was worked and marks the days where
the stakes were highest. What that should have paid is yours to work out — a confidently
wrong number would be the exact failure this is meant to catch.

## Design constraints

Built for a road flagger's day, which shapes nearly every decision:

- Start is fixed (7:00 AM), finish varies from early afternoon to past 6:00 PM
- Worked through lunch, paid through it — no break to subtract
- A minimum 8 hours is paid regardless of a short day, so precision only matters
  on long ones
- Time-and-a-half past 9 hours, which is where a missing half hour costs real money
- Read outdoors, in daylight glare, one-handed and possibly gloved

## Repository

| Path | Contents |
|---|---|
| `design-spec.md` | Design system — palette, type, spacing, components, anti-patterns, open questions |
| `design/hour-log-mockup.html` | Three screens rendered with the spec's tokens |
| `design/check-contrast.py` | Verifies the palette against a 4.5:1 contrast floor |

No application code yet. The design foundation is settled; the location-inference
approach is being validated against real field data before anything is built on it.
