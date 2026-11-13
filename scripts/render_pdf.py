#!/usr/bin/env python3
"""Render selected one-based PDF pages for visual proofreading (requires pymupdf)."""
import argparse
from pathlib import Path

import pymupdf

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("pdf", type=Path)
parser.add_argument("--pages", type=int, nargs="+")
parser.add_argument("--scale", type=float, default=1.5)
parser.add_argument("--output", type=Path, default=Path("tmp/pdfs"))
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=True)
with pymupdf.open(args.pdf) as document:
    for page in args.pages or range(1, len(document) + 1):
        document[page - 1].get_pixmap(
            matrix=pymupdf.Matrix(args.scale, args.scale), alpha=False
        ).save(args.output / f"{args.pdf.stem}-{page:02}.png")
