#!/usr/bin/env python3
"""Combine .cpp files into a single PDF. Requires: pip install reportlab."""

import argparse
from pathlib import Path
import sys
import textwrap


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "directory", nargs="?", type=Path, default=Path.cwd(),
        help="directory to search recursively (default: current directory)",
    )
    parser.add_argument(
        "-o", "--output", type=Path, default=Path("combined_cpp.pdf"),
        help="output PDF path (default: combined_cpp.pdf)",
    )
    args = parser.parse_args()
    directory = args.directory.resolve()
    if not directory.is_dir():
        parser.error(f"Not a directory: {directory}")
    sources = sorted(directory.rglob("*.cpp"))
    if not sources:
        parser.error(f"No .cpp files found in {directory}")

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
    except ImportError:
        parser.exit(1, "Missing dependency. Install it with: python3 -m pip install reportlab\n")

    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    document = canvas.Canvas(str(output), pagesize=A4)
    document.setTitle("Combined C++ source files")
    width, height = A4
    margin = 36
    font_size = 8
    line_height = 11
    page_number = 0
    wrapper = textwrap.TextWrapper(
        width=int((width - 2 * margin) / (font_size * 0.6)),
        expand_tabs=False,
        replace_whitespace=False,
        drop_whitespace=False,
    )

    def start_page(filename):
        nonlocal page_number
        if page_number:
            document.showPage()
        page_number += 1
        document.setFont("Helvetica-Bold", 10)
        heading_lines = textwrap.wrap(filename, width=80) or [filename]
        position = height - margin
        for heading in heading_lines:
            document.drawString(margin, position, heading)
            position -= 12
        document.setFont("Helvetica", 8)
        document.drawRightString(width - margin, 20, f"Page {page_number}")
        document.setFont("Courier", font_size)
        return position - 12

    try:
        for source in sources:
            filename = source.relative_to(directory).as_posix()
            position = start_page(filename)
            content = source.read_text(encoding="utf-8", errors="replace")
            for line_number, line in enumerate(content.splitlines(), start=1):
                numbered_line = f"{line_number:5}  {line.expandtabs(4)}"
                for fragment in wrapper.wrap(numbered_line):
                    if position < margin:
                        position = start_page(filename)
                    document.drawString(margin, position, fragment)
                    position -= line_height
        document.save()
    except OSError as error:
        parser.exit(1, f"Could not create PDF: {error}\n")

    print(f"Combined {len(sources)} .cpp files into {output}")


if __name__ == "__main__":
    main()
