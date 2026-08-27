#!/usr/bin/env python3
"""Recover a work day from a GPS trace by finding the drives that bracket it.

The premise, in one line: the work day is the gap between the end of the
morning drive and the start of the evening drive.

This deliberately avoids geofencing. A geofence has to know where the site is,
which is the one thing we cannot rely on -- a flagging site shifts a few hundred
feet along the road day to day, and the parking spot varies. Detecting the
*transition* out of driving sidesteps all of it:

    driving      15 - 25 m/s
    walking       1.2 - 1.5 m/s
    standing      0 - 1 m/s (mostly GPS jitter)

The gap between the fastest thing you do at work and the slowest thing you do
getting there is about tenfold, which is a far more forgiving signal than any
boundary drawn on a map. It also means the phone can ride in the truck or in a
pocket without changing the answer, and the walk from the truck to the flagging
position lands inside the window automatically.

Usage:
    python3 analysis/segment.py <trace.gpx> [--start-hhmm 0700] [--end-hhmm 1712]

Passing the ground-truth times reports the error against them, which is the
whole point of field test 01 (see ../research/field-test-01.md).
"""

import argparse
import math
import statistics
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

# --- Thresholds -------------------------------------------------------------
# The margin that matters is against WALKING, not against highway speed.
#
# This started at 8.0 m/s, reasoned from open-road driving, and that was wrong
# for the commute it has to detect: a 5 minute, 2.2 km drive through town
# averages 7.3 m/s and never sustains 8, so the day could not be bracketed at
# all. The detector found zero drives and declined -- correctly, but uselessly.
#
#     walking          1.2 - 1.5 m/s
#     brisk walk       ~2.0 m/s
#     THRESHOLD        4.5 m/s  (16 km/h)
#     slow town drive  7 - 11 m/s
#     open road        15 - 25 m/s
#
# 4.5 m/s keeps a threefold margin over walking -- still an enormous gap, since
# nobody walks to a job site at 16 km/h -- while catching a slow commute that
# barely gets above town speed. Raising this to "be safe" is what broke it.
DRIVE_SPEED_MS = 4.5

# A drive only counts as a commute if it is both sustained and goes somewhere.
# Both conditions are needed: repositioning a truck 200 m along the work zone
# can exceed the speed threshold briefly, and would otherwise split the day in
# two. Requiring real displacement rejects it.
#
# These are sized for a SHORT commute. The real one being tested is 5-10
# minutes door to door, so a threshold tuned to a half-hour drive would reject
# the very trip the whole method depends on. Speed does the discriminating
# here, not distance -- walking never approaches 8 m/s no matter how far it
# goes -- so both bounds can sit low without letting a walk through.
MIN_DRIVE_SECONDS = 90
MIN_DRIVE_DISPLACEMENT_M = 1000

# Odd samples spike to absurd speeds when a fix is poor. A rolling median over
# an odd-sized window removes them without smearing genuine transitions the way
# a mean would.
#
# The window must be chosen in SECONDS, not samples. A fixed 5-sample window is
# 50 s of smoothing at a 10 s logging interval and a full 5 minutes at 60 s --
# and 5 minutes of smoothing applied to a 6 minute commute erases the commute.
# That failure is silent: the trace looks fine, the drive simply vanishes.
SMOOTHING_SECONDS = 90
MIN_SMOOTHING_WINDOW = 3
MAX_SMOOTHING_WINDOW = 9

# Sanity checks on the recovered window.
MIN_WORKDAY_SECONDS = 3 * 3600
MAX_SITE_RADIUS_M = 800.0

EARTH_RADIUS_M = 6371000.0

GPX_NS = {"gpx": "http://www.topografix.com/GPX/1/1"}


# --- Geometry ---------------------------------------------------------------

def haversine(lat1, lon1, lat2, lon2):
    """Great-circle distance in metres."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


# --- Parsing ----------------------------------------------------------------

def parse_gpx(path):
    """Return [(datetime, lat, lon), ...] sorted by time.

    Handles both namespaced GPX 1.1 and the un-namespaced files some loggers
    emit, because it is not worth losing a day of fieldwork to an XML detail.
    """
    tree = ET.parse(path)
    root = tree.getroot()

    points = root.findall(".//gpx:trkpt", GPX_NS)
    if not points:
        points = root.findall(".//trkpt")
    if not points:
        raise SystemExit(f"{path}: no <trkpt> elements found")

    out = []
    for pt in points:
        time_el = pt.find("gpx:time", GPX_NS)
        if time_el is None:
            time_el = pt.find("time")
        if time_el is None or not time_el.text:
            continue
        raw = time_el.text.strip().replace("Z", "+00:00")
        when = datetime.fromisoformat(raw)
        if when.tzinfo is None:
            when = when.replace(tzinfo=timezone.utc)
        out.append((when, float(pt.get("lat")), float(pt.get("lon"))))

    out.sort(key=lambda p: p[0])
    return out


# --- Segmentation -----------------------------------------------------------

def point_speeds(points):
    """Instantaneous speed (m/s) at each point, from the step that precedes it."""
    speeds = [0.0]
    for i in range(1, len(points)):
        (t0, la0, lo0), (t1, la1, lo1) = points[i - 1], points[i]
        dt = (t1 - t0).total_seconds()
        if dt <= 0:
            speeds.append(speeds[-1])
            continue
        speeds.append(haversine(la0, lo0, la1, lo1) / dt)
    return speeds


def sample_interval(points):
    """Median seconds between samples. Loggers drift, so take the median."""
    gaps = [(points[i][0] - points[i - 1][0]).total_seconds()
            for i in range(1, len(points))]
    gaps = [g for g in gaps if g > 0]
    return statistics.median(gaps) if gaps else 1.0


def smoothing_window(points):
    """An odd sample count covering roughly SMOOTHING_SECONDS of real time."""
    n = int(round(SMOOTHING_SECONDS / sample_interval(points)))
    n = max(MIN_SMOOTHING_WINDOW, min(MAX_SMOOTHING_WINDOW, n))
    return n if n % 2 else n + 1


def rolling_median(values, window):
    half = window // 2
    return [
        statistics.median(values[max(0, i - half):min(len(values), i + half + 1)])
        for i in range(len(values))
    ]


def find_drives(points, speeds):
    """Contiguous runs above the drive threshold that are sustained and go somewhere.

    Returns [(start_index, end_index), ...] inclusive.
    """
    runs = []
    start = None
    for i, speed in enumerate(speeds):
        if speed >= DRIVE_SPEED_MS:
            if start is None:
                start = i
        elif start is not None:
            runs.append((start, i - 1))
            start = None
    if start is not None:
        runs.append((start, len(speeds) - 1))

    qualified = []
    for a, b in runs:
        duration = (points[b][0] - points[a][0]).total_seconds()
        displacement = haversine(points[a][1], points[a][2], points[b][1], points[b][2])
        if duration >= MIN_DRIVE_SECONDS and displacement >= MIN_DRIVE_DISPLACEMENT_M:
            qualified.append((a, b))
    return qualified


def spread(points, lo, hi):
    """Centroid and radius of gyration (m) over points[lo:hi+1]."""
    window = points[lo:hi + 1]
    clat = sum(p[1] for p in window) / len(window)
    clon = sum(p[2] for p in window) / len(window)
    sq = [haversine(clat, clon, p[1], p[2]) ** 2 for p in window]
    return clat, clon, math.sqrt(sum(sq) / len(sq)), max(math.sqrt(s) for s in sq)


def infer_workday(points):
    """Infer the work window. Returns a result dict; 'ok' says whether to trust it."""
    if len(points) < MIN_SMOOTHING_WINDOW:
        return {"ok": False, "reason": "trace too short to segment"}

    interval = sample_interval(points)
    window = smoothing_window(points)
    speeds = rolling_median(point_speeds(points), window)
    drives = find_drives(points, speeds)

    if len(drives) < 2:
        reason = (
            f"found {len(drives)} qualifying drive(s), need 2 to bracket a day. "
            "Recording likely started after arriving or stopped before leaving."
        )
        # A short commute logged coarsely is the other way this fails, and it
        # looks identical from the outside. Say so rather than let it be
        # misdiagnosed as a forgotten logger.
        if interval > 20:
            reason += (
                f" Sampling every {interval:.0f}s may also be too coarse to catch a "
                "commute of only a few minutes -- try a 10s interval."
            )
        return {"ok": False, "reason": reason, "drives": drives}

    # First drive of the day ends at the parking event; last drive begins at departure.
    arrive_i = drives[0][1]
    depart_i = drives[-1][0]
    interior = drives[1:-1]

    if depart_i <= arrive_i:
        return {"ok": False, "reason": "drives overlap; cannot bracket a window"}

    duration = (points[depart_i][0] - points[arrive_i][0]).total_seconds()
    clat, clon, radius, furthest = spread(points, arrive_i, depart_i)

    warnings = []
    if duration < MIN_WORKDAY_SECONDS:
        warnings.append(f"window is only {duration / 3600:.1f} h")
    if radius > MAX_SITE_RADIUS_M:
        warnings.append(
            f"site radius {radius:.0f} m exceeds {MAX_SITE_RADIUS_M:.0f} m -- "
            "possibly two sites in one day"
        )
    if interior:
        warnings.append(
            f"{len(interior)} qualifying drive(s) inside the window -- "
            "moved between locations mid-shift?"
        )

    # The bracketing drives are the whole mechanism. If either is carried by only
    # a handful of samples, the inferred times are resting on very little.
    thin = min(drives[0][1] - drives[0][0] + 1, drives[-1][1] - drives[-1][0] + 1)
    if thin < 8:
        warnings.append(
            f"shortest bracketing drive has only {thin} samples -- "
            "log more often for a commute this short"
        )

    return {
        "ok": True,
        "sample_interval_s": interval,
        "smoothing_window": window,
        "arrived": points[arrive_i][0],
        "departed": points[depart_i][0],
        "duration_h": duration / 3600,
        "centroid": (clat, clon),
        "radius_m": radius,
        "furthest_m": furthest,
        "drives": drives,
        "interior_drives": interior,
        "warnings": warnings,
        "samples": len(points),
    }


# --- Reporting --------------------------------------------------------------

def local_hhmm(dt):
    return dt.astimezone().strftime("%H:%M")


def compare(label, inferred, truth_hhmm):
    """Report inferred vs a ground-truth HHMM on the same local date."""
    hh, mm = int(truth_hhmm[:2]), int(truth_hhmm[2:])
    local = inferred.astimezone()
    truth = local.replace(hour=hh, minute=mm, second=0, microsecond=0)
    delta_min = (local - truth).total_seconds() / 60
    verdict = "good" if abs(delta_min) <= 5 else "MISS" if abs(delta_min) > 15 else "near"
    sign = "+" if delta_min >= 0 else ""
    print(f"  {label:<10} inferred {local_hhmm(inferred)}   "
          f"actual {truth.strftime('%H:%M')}   {sign}{delta_min:.0f} min   {verdict}")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("gpx")
    ap.add_argument("--start-hhmm", help="ground-truth start, e.g. 0700")
    ap.add_argument("--end-hhmm", help="ground-truth finish, e.g. 1712")
    args = ap.parse_args()

    points = parse_gpx(args.gpx)
    result = infer_workday(points)

    print(f"\n{args.gpx}")
    print(f"  {len(points)} samples, "
          f"{local_hhmm(points[0][0])} to {local_hhmm(points[-1][0])}")
    print()

    if not result["ok"]:
        print(f"  Could not infer a work day: {result['reason']}")
        return 1

    print(f"  Parked     {local_hhmm(result['arrived'])}")
    print(f"  Left       {local_hhmm(result['departed'])}")
    print(f"  On site    {result['duration_h']:.2f} h")
    print(f"  Site       {result['radius_m']:.0f} m radius, "
          f"{result['furthest_m']:.0f} m furthest excursion")

    if result["warnings"]:
        print()
        for w in result["warnings"]:
            print(f"  warning: {w}")

    if args.start_hhmm or args.end_hhmm:
        print("\n  Against ground truth")
        if args.start_hhmm:
            compare("start", result["arrived"], args.start_hhmm)
        if args.end_hhmm:
            compare("finish", result["departed"], args.end_hhmm)

    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
