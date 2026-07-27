# Formatting options

Options the PDF exporter understands. The demo `scripts/export.py` implements a
minimal subset; a production exporter would expand these into real layout controls.
This file documents the intended surface so the skill's "read references/formatting.md"
step resolves.

| Option | Values | Default | Notes |
|--------|--------|---------|-------|
| Page size | `letter`, `a4` | `letter` (612×792 pt) | Sets the PDF MediaBox. |
| Font | `Courier`, `Helvetica`, `Times-Roman` | `Courier` | Any Base-14 PDF font. |
| Font size | points | `11` | Body text size. |
| Margin | points | `56` (~0.78 in) | Left/top text origin. |

The demo script hardcodes Courier / letter / 11 pt for simplicity. Change the
defaults in `scripts/export.py` (the `build_pdf` function) to adjust them.
