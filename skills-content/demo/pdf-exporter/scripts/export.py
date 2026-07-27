#!/usr/bin/env python3
"""Minimal Markdown-to-PDF exporter for the pdf-exporter demo skill.

Dependency-free: emits a valid single-page PDF containing the report text so
the demo is forkable and runnable with nothing but python3. This is a demo
stub, not a production renderer. See ../references/formatting.md for the
formatting options a real implementation would expose.

Usage: python3 export.py <input.md> <output.pdf>
"""
import sys
from pathlib import Path


def _escape(s: str) -> str:
    return s.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")


def build_pdf(lines):
    """Render lines as monospaced text into a valid PDF byte string."""
    parts = ["BT", "/F1 11 Tf", "12 TL", "1 0 0 1 56 760 Tm"]
    for line in lines:
        parts.append(f"({_escape(line[:95])}) Tj")
        parts.append("T*")
    parts.append("ET")
    content = "\n".join(parts).encode("latin-1", "replace")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>",
        b"<< /Length " + str(len(content)).encode() + b" >>\nstream\n" + content + b"\nendstream",
    ]

    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode() + obj + b"\nendobj\n"
    xref_pos = len(out)
    out += f"xref\n0 {len(objects) + 1}\n".encode()
    out += b"0000000000 65535 f \n"
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode()
    out += (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_pos}\n%%EOF\n"
    ).encode()
    return bytes(out)


def main():
    if len(sys.argv) != 3:
        sys.exit("Usage: python3 export.py <input.md> <output.pdf>")
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    lines = src.read_text(encoding="utf-8").splitlines() or ["(empty document)"]
    dst.write_bytes(build_pdf(lines))
    print(dst)


if __name__ == "__main__":
    main()
