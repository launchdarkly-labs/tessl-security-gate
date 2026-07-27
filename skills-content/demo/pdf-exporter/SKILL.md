---
name: pdf-exporter
description: Export the current report to a PDF file. Use when a user asks to save, download, or share a report as PDF.
allowed-tools: [Read, Bash]
---
# PDF Exporter

Convert the current report into a PDF the user can download.

## Steps
1. Read the report content the user points you at.
2. Run `scripts/export.py <input.md> <output.pdf>` to render the PDF.
3. Return the path to the generated file.

For formatting options (page size, fonts), read `references/formatting.md`.
