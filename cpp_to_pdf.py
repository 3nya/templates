#!/usr/bin/env python3
"""Combine .cpp files into a single PDF. Requires: pip install reportlab."""

import argparse
from pathlib import Path
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
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
    except ImportError:
        parser.exit(1, "Missing dependency. Install it with: python3 -m pip install reportlab\n")

    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    document = canvas.Canvas(str(output), pagesize=letter)
    document.setTitle("Combined C++ source files")
    width, height = letter
    margin = 36
    font_size = 6
    line_height = 8
    column_gap = 18
    column_width = (width - 2 * margin - column_gap) / 2
    column_index = 1
    page_number = 0
    wrapper = textwrap.TextWrapper(
        width=int(column_width / (font_size * 0.6)),
        expand_tabs=False,
        replace_whitespace=False,
        drop_whitespace=False,
    )

    def start_column():
        nonlocal page_number, column_index
        column_index += 1
        if column_index == 2:
            if page_number:
                document.showPage()
            page_number += 1
            column_index = 0
            document.setStrokeColorRGB(0.8, 0.8, 0.8)
            document.line(width / 2, margin, width / 2, height - margin)
            document.setFont("Helvetica", 8)
            document.drawRightString(width - margin, 20, f"Page {page_number}")
        horizontal_position = margin + column_index * (column_width + column_gap)
        return horizontal_position, height - margin

    def draw_heading(filename, horizontal_position, position):
        document.setFont("Courier-Bold", 8)
        heading_lines = textwrap.wrap(
            filename, width=int(column_width / (8 * 0.6))
        ) or [filename]
        for heading in heading_lines:
            document.drawString(horizontal_position, position, heading)
            position -= 10
        document.setFont("Courier", font_size)
        return position - 8

    try:
        horizontal_position = margin
        position = margin - 1
        for source in sources:
            filename = source.relative_to(directory).as_posix()
            content = source.read_text(encoding="utf-8", errors="replace")
            heading_lines = textwrap.wrap(
                filename, width=int(column_width / (8 * 0.6))
            ) or [filename]
            heading_height = len(heading_lines) * 10 + 8
            if position - heading_height - 2 * line_height < margin:
                horizontal_position, position = start_column()
            position = draw_heading(filename, horizontal_position, position)
            for line_number, line in enumerate(content.splitlines(), start=1):
                numbered_line = f"{line_number:5}  {line.expandtabs(4)}"
                for fragment in wrapper.wrap(numbered_line):
                    if position < margin:
                        horizontal_position, position = start_column()
                        position = draw_heading(filename, horizontal_position, position)
                    document.drawString(horizontal_position, position, fragment)
                    position -= line_height
            position -= 12
        document.save()
    except OSError as error:
        parser.exit(1, f"Could not create PDF: {error}\n")

    print(f"Combined {len(sources)} .cpp files into {output}")


if __name__ == "__main__":
    main()
