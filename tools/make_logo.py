#!/usr/bin/env python3
"""Generate the official Clew logo.

Do not edit assets/clew.svg directly.
Edit the LOGO_SPEC values below and regenerate instead.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LogoSpec:
    """Visual constants used to construct the canonical Clew logo."""

    canvas: int = 256
    stroke_width: int = 18
    colour: str = "#000000"

    # Main diagonal strokes
    long_length: int = 118
    long_spacing: int = 31

    # Short binding strokes
    short_length: int = 38

    # Dots
    dot_radius: int = 9

    # Loose thread
    tail_gap: int = 16


SPEC = LogoSpec()


def rotate_point(
    x: float,
    y: float,
    angle_degrees: float,
    cx: float,
    cy: float,
) -> tuple[float, float]:
    """Rotate a point around a centre."""
    angle = math.radians(angle_degrees)
    dx = x - cx
    dy = y - cy

    rx = dx * math.cos(angle) - dy * math.sin(angle)
    ry = dx * math.sin(angle) + dy * math.cos(angle)

    return cx + rx, cy + ry


def line_segment(
    cx: float,
    cy: float,
    length: float,
    angle_degrees: float,
) -> tuple[float, float, float, float]:
    """Return x1, y1, x2, y2 for a centred line segment."""
    half = length / 2
    x1, y1 = cx - half, cy
    x2, y2 = cx + half, cy

    x1, y1 = rotate_point(x1, y1, angle_degrees, cx, cy)
    x2, y2 = rotate_point(x2, y2, angle_degrees, cx, cy)

    return x1, y1, x2, y2


def path_line(x1: float, y1: float, x2: float, y2: float) -> str:
    """SVG path for a straight stroke."""
    return f'<path d="M{x1:.1f} {y1:.1f} L{x2:.1f} {y2:.1f}" />'


def circle(cx: float, cy: float, r: float) -> str:
    """SVG circle."""
    return (
        f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" '
        f'fill="{SPEC.colour}" stroke="none" />'
    )


def build_svg(spec: LogoSpec) -> str:
    """Build the complete SVG document for a logo specification."""
    angle = -45
    cx = cy = spec.canvas / 2

    elements: list[str] = []

    # Three main strands
    for offset in (-spec.long_spacing, 0, spec.long_spacing):
        x1, y1, x2, y2 = line_segment(cx, cy + offset, spec.long_length, angle)
        elements.append(path_line(x1, y1, x2, y2))

    # Upper-left short binding strands
    for x, y in [
        (72, 104),
        (91, 84),
        (112, 66),
    ]:
        x1, y1, x2, y2 = line_segment(x, y, spec.short_length, angle)
        elements.append(path_line(x1, y1, x2, y2))

    # Lower-right short binding strands
    for x, y in [
        (146, 190),
        (168, 171),
    ]:
        x1, y1, x2, y2 = line_segment(x, y, spec.short_length, angle)
        elements.append(path_line(x1, y1, x2, y2))

    # Dots completing the implied clew
    elements.append(circle(59, 137, spec.dot_radius))
    elements.append(circle(130, 67, spec.dot_radius))
    elements.append(circle(116, 205, spec.dot_radius))

    # Loose thread, deliberately separate from the weave
    elements.append(
        '<path d="M190 160 C215 185 198 211 174 215 C155 218 151 238 166 244" />'
    )

    body = "\n    ".join(elements)

    return f'''<svg xmlns="http://www.w3.org/2000/svg" \
viewBox="0 0 {spec.canvas} {spec.canvas}" role="img" aria-label="Clew logo">
  <g fill="none" stroke="{spec.colour}" stroke-width="{spec.stroke_width}" \
stroke-linecap="round" stroke-linejoin="round">
    {body}
  </g>
</svg>
'''


def main() -> None:
    """Regenerate the checked-in SVG asset from the logo specification."""
    repo_root = Path(__file__).resolve().parents[1]
    output = repo_root / "assets" / "clew.svg"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(build_svg(SPEC), encoding="utf-8")
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
