#!/usr/bin/env python3
"""Verify every text pair in the Hour Log palette against the 4.5:1 floor.

The design spec (../design-spec.md) claims specific contrast ratios and sets a
hard rule that no text tier may fall below 4.5:1 -- the app is read outdoors in
daylight glare, where the WCAG minimum is a floor rather than a target.

Run this after any palette change:  python3 design/check-contrast.py
Exits non-zero if any text pair fails.
"""

import sys

FLOOR = 4.5          # all text, including muted
FLOOR_NONTEXT = 3.0  # UI marks that carry meaning but no words


def _linear(channel: int) -> float:
    c = channel / 255
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def luminance(hex_color: str) -> float:
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * _linear(r) + 0.7152 * _linear(g) + 0.0722 * _linear(b)


def ratio(fg: str, bg: str) -> float:
    a, b = luminance(fg), luminance(bg)
    hi, lo = max(a, b), min(a, b)
    return (hi + 0.05) / (lo + 0.05)


LIGHT = {
    "bg": "#FCFCFA",
    "surface": "#FFFFFF",
    "text": "#1A1815",
    "text-muted": "#746B5E",
    "primary": "#F25C05",
    "primary-ink": "#9E3B00",
    "primary-subtle": "#FDEEE3",
    "on-primary": "#1A1815",
    "error": "#B3261E",
}

DARK = {
    "bg": "#171512",
    "surface": "#1E1B18",
    "text": "#F2EFE9",
    "text-muted": "#948C80",
    "primary": "#FF7A22",
    "primary-ink": "#FF9A52",
    "primary-subtle": "#2E1D10",
    "on-primary": "#1A1815",
    "error": "#FF6B5E",
}

# (foreground token, background token, is_text)
PAIRS = [
    ("text", "bg", True),
    ("text", "surface", True),
    ("text", "primary-subtle", True),
    ("text-muted", "bg", True),
    ("text-muted", "surface", True),
    ("text-muted", "primary-subtle", True),
    ("primary-ink", "bg", True),
    ("primary-ink", "primary-subtle", True),
    ("on-primary", "primary", True),
    ("error", "bg", True),
    # The raw accent carries the long-day stripe and the pending pill fill.
    # It is a mark, not a word -- 3:1 is the applicable floor, and it must
    # never be used for text (see design-spec.md sec. 2).
    ("primary", "bg", False),
]


def check(theme_name: str, tokens: dict) -> list:
    failures = []
    print(f"\n{theme_name}")
    print("-" * 58)
    for fg, bg, is_text in PAIRS:
        r = ratio(tokens[fg], tokens[bg])
        floor = FLOOR if is_text else FLOOR_NONTEXT
        ok = r >= floor
        mark = "ok  " if ok else "FAIL"
        kind = "" if is_text else "  (mark)"
        print(f"  {mark}  {fg:>14} on {bg:<16} {r:5.2f}  (>= {floor}){kind}")
        if not ok:
            failures.append(f"{theme_name}: {fg} on {bg} = {r:.2f}, needs {floor}")
    return failures


def main() -> int:
    failures = check("LIGHT", LIGHT) + check("DARK", DARK)
    print()
    if failures:
        for f in failures:
            print(f"FAIL  {f}")
        return 1
    print("All pairs pass.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
