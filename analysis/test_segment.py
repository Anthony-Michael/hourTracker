#!/usr/bin/env python3
"""Synthetic days with known answers, to check the segmenter before real data lands.

Every scenario here is built from a stated ground truth, so the segmenter's
output can be checked rather than eyeballed. This is not a substitute for field
test 01 -- synthetic GPS is far cleaner than the real thing, and passing here
only means the logic is sound, not that it survives a real trace.

Run:  python3 analysis/test_segment.py
"""

import math
import os
import random
import sys
import tempfile
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from segment import infer_workday, parse_gpx  # noqa: E402

# A rural two-lane somewhere in the Fraser Valley. Any coordinates would do;
# these keep the metres-per-degree conversion honest at a realistic latitude.
SITE_LAT, SITE_LON = 49.2043, -122.8017
DAY = datetime(2026, 8, 26, tzinfo=timezone.utc)
SAMPLE_SECONDS = 60

random.seed(20260826)


def offset(lat, lon, north_m, east_m):
    dlat = north_m / 111320.0
    dlon = east_m / (111320.0 * math.cos(math.radians(lat)))
    return lat + dlat, lon + dlon


def at(hhmm, second=0):
    return DAY.replace(hour=int(hhmm[:2]), minute=int(hhmm[2:]), second=second)


def drive(points, start, end, from_pt, to_pt):
    """Straight-line travel, sampled every minute, with mild speed variation."""
    total = (end - start).total_seconds()
    steps = max(1, int(total // SAMPLE_SECONDS))
    for i in range(steps + 1):
        f = i / steps
        lat = from_pt[0] + (to_pt[0] - from_pt[0]) * f
        lon = from_pt[1] + (to_pt[1] - from_pt[1]) * f
        jitter_n = random.gauss(0, 4)
        jitter_e = random.gauss(0, 4)
        lat, lon = offset(lat, lon, jitter_n, jitter_e)
        points.append((start + timedelta(seconds=i * SAMPLE_SECONDS), lat, lon))


def stand(points, start, end, centre, drift_m=200.0, jitter_m=25.0):
    """A flagger's day: near-stationary, but the work zone creeps along the road."""
    total = (end - start).total_seconds()
    steps = max(1, int(total // SAMPLE_SECONDS))
    for i in range(steps + 1):
        f = i / steps
        lat, lon = offset(centre[0], centre[1], 0, drift_m * f)
        lat, lon = offset(lat, lon, random.gauss(0, jitter_m), random.gauss(0, jitter_m))
        points.append((start + timedelta(seconds=i * SAMPLE_SECONDS), lat, lon))


def write_gpx(points, path):
    with open(path, "w") as fh:
        fh.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        fh.write('<gpx version="1.1" creator="test_segment" '
                 'xmlns="http://www.topografix.com/GPX/1/1">\n<trk><trkseg>\n')
        for when, lat, lon in points:
            fh.write(f'<trkpt lat="{lat:.7f}" lon="{lon:.7f}">'
                     f'<time>{when.strftime("%Y-%m-%dT%H:%M:%SZ")}</time></trkpt>\n')
        fh.write("</trkseg></trk></gpx>\n")


# --- Scenarios --------------------------------------------------------------

def normal_day():
    """Short day: parked 06:47, finished 13:05. Paid 8 regardless, so precision
    here barely matters -- but it must not produce nonsense."""
    home = offset(SITE_LAT, SITE_LON, 12000, 18000)
    lot = offset(SITE_LAT, SITE_LON, -30, -240)
    pts = []
    drive(pts, at("0620"), at("0647"), home, lot)
    drive(pts, at("0647"), at("0653"), lot, (SITE_LAT, SITE_LON))   # walk in
    stand(pts, at("0653"), at("1259"), (SITE_LAT, SITE_LON))
    drive(pts, at("1259"), at("1305"), (SITE_LAT, SITE_LON), lot)   # walk out
    drive(pts, at("1305"), at("1334"), lot, home)
    return pts, "0647", "1305"


def overtime_day():
    """The day that matters: 10.4 hours, well past the 9-hour threshold."""
    home = offset(SITE_LAT, SITE_LON, 12000, 18000)
    lot = offset(SITE_LAT, SITE_LON, 40, 310)
    pts = []
    drive(pts, at("0618"), at("0645"), home, lot)
    drive(pts, at("0645"), at("0652"), lot, (SITE_LAT, SITE_LON))
    stand(pts, at("0652"), at("1704"), (SITE_LAT, SITE_LON), drift_m=340)
    drive(pts, at("1704"), at("1712"), (SITE_LAT, SITE_LON), lot)
    drive(pts, at("1712"), at("1745"), lot, home)
    return pts, "0645", "1712"


def truck_repositioned():
    """The work zone moves and the truck moves with it, 600 m up the road at
    midday. This must NOT split the day into two -- it is the failure mode the
    displacement and duration filters exist to prevent."""
    home = offset(SITE_LAT, SITE_LON, 12000, 18000)
    lot = offset(SITE_LAT, SITE_LON, 0, -200)
    second = offset(SITE_LAT, SITE_LON, 0, 600)
    pts = []
    drive(pts, at("0620"), at("0648"), home, lot)
    stand(pts, at("0648"), at("1200"), (SITE_LAT, SITE_LON), drift_m=120)
    drive(pts, at("1200"), at("1201"), (SITE_LAT, SITE_LON), second)  # 600 m hop
    stand(pts, at("1201"), at("1638"), second, drift_m=120)
    drive(pts, at("1638"), at("1712"), second, home)
    return pts, "0648", "1638"


def started_recording_late():
    """He forgot to start the logger until he was already on site. There is no
    morning drive to bracket against, so the honest answer is 'I cannot tell' --
    not a confident guess."""
    home = offset(SITE_LAT, SITE_LON, 12000, 18000)
    pts = []
    stand(pts, at("0812"), at("1630"), (SITE_LAT, SITE_LON))
    drive(pts, at("1630"), at("1702"), (SITE_LAT, SITE_LON), home)
    return pts, None, None


def walks_off_site():
    """Twice in the day he walks a few blocks to the porta potty and back.

    This is the case that would sink a geofence: a 350 m excursion crosses any
    plausible site boundary and reads as 'left the site' at ten in the morning.
    Bracketing on commutes cannot see it -- walking is ~1.4 m/s, six times under
    the driving threshold -- so the day stays whole."""
    home = offset(SITE_LAT, SITE_LON, 12000, 18000)
    lot = offset(SITE_LAT, SITE_LON, 0, -180)
    potty = offset(SITE_LAT, SITE_LON, 310, -160)
    pts = []
    drive(pts, at("0621"), at("0649"), home, lot)
    stand(pts, at("0649"), at("1002"), (SITE_LAT, SITE_LON), drift_m=90)
    drive(pts, at("1002"), at("1006"), (SITE_LAT, SITE_LON), potty)     # walk out
    stand(pts, at("1006"), at("1012"), potty, drift_m=0, jitter_m=8)
    drive(pts, at("1012"), at("1016"), potty, (SITE_LAT, SITE_LON))     # walk back
    stand(pts, at("1016"), at("1428"), (SITE_LAT, SITE_LON), drift_m=90)
    drive(pts, at("1428"), at("1432"), (SITE_LAT, SITE_LON), potty)
    stand(pts, at("1432"), at("1438"), potty, drift_m=0, jitter_m=8)
    drive(pts, at("1438"), at("1442"), potty, (SITE_LAT, SITE_LON))
    stand(pts, at("1442"), at("1707"), (SITE_LAT, SITE_LON), drift_m=90)
    drive(pts, at("1707"), at("1739"), (SITE_LAT, SITE_LON), home)
    return pts, "0649", "1707"


SCENARIOS = [
    ("normal short day", normal_day, True),
    ("overtime day", overtime_day, True),
    ("truck repositioned mid-shift", truck_repositioned, True),
    ("walks off site to the porta potty", walks_off_site, True),
    ("logger started late", started_recording_late, False),
]

TOLERANCE_MIN = 5


def main():
    tmp = tempfile.mkdtemp(prefix="hourlog-")
    failures = []

    for name, build, should_infer in SCENARIOS:
        points, truth_start, truth_end = build()
        path = os.path.join(tmp, name.replace(" ", "_") + ".gpx")
        write_gpx(points, path)
        result = infer_workday(parse_gpx(path))

        print(f"\n{name}")
        print("-" * 60)

        if not should_infer:
            if result["ok"]:
                print("  FAIL  inferred a day it should have refused")
                failures.append(name)
            else:
                print(f"  ok    declined, as it should: {result['reason']}")
            continue

        if not result["ok"]:
            print(f"  FAIL  could not infer: {result['reason']}")
            failures.append(name)
            continue

        for label, inferred, truth in (
            ("parked", result["arrived"], truth_start),
            ("left", result["departed"], truth_end),
        ):
            want = at(truth)
            err = (inferred - want).total_seconds() / 60
            ok = abs(err) <= TOLERANCE_MIN
            mark = "ok  " if ok else "FAIL"
            print(f"  {mark}  {label:<7} {inferred.strftime('%H:%M')} "
                  f"vs {want.strftime('%H:%M')}   {err:+.0f} min")
            if not ok:
                failures.append(f"{name}/{label}")

        print(f"        {result['duration_h']:.2f} h on site, "
              f"{result['radius_m']:.0f} m radius")
        for w in result["warnings"]:
            print(f"        warning: {w}")

    print()
    if failures:
        print(f"{len(failures)} failure(s): {', '.join(failures)}")
        return 1
    print(f"All {len(SCENARIOS)} scenarios behaved as intended.")
    print("Synthetic GPS is cleaner than real GPS. This proves the logic, not the product.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
