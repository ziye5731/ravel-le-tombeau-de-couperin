#!/usr/bin/env python3
"""Compile the editable piano score to PDF and MIDI with LilyPond."""
from pathlib import Path
import argparse
import os
import shutil
import subprocess
import sys
from midi_files import concatenate

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "pdf"
MIDI_OUT = ROOT / "output" / "midi"
MOVEMENTS = ["01-prelude", "02-fugue", "03-forlane", "04-rigaudon", "05-menuet", "06-toccata"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--midi-only", action="store_true", help="Generate MIDI without writing PDF")
    parser.add_argument("sources", nargs="*", help="Movement .ly filenames; default: the complete suite")
    args = parser.parse_args()
    lilypond = shutil.which("lilypond")
    if not lilypond:
        sys.exit("LilyPond is required (tested with 2.26.0).")
    OUT.mkdir(parents=True, exist_ok=True)
    MIDI_OUT.mkdir(parents=True, exist_ok=True)
    target = MIDI_OUT if args.midi_only else OUT
    cache = ROOT / "tmp" / "cache"
    cache.mkdir(parents=True, exist_ok=True)
    sources = [ROOT / "piano" / "lilypond" / "le-tombeau-de-couperin.ly"]
    if args.sources:
        sources = [ROOT / "piano" / "lilypond" / name for name in args.sources]
    for source in sources:
        subprocess.run(
            [lilypond, "-dno-point-and-click", *(["-dno-print-pages"] if args.midi_only else []),
             "-o", str(target / source.stem), str(source)],
            cwd=source.parent,
            env={**os.environ, "XDG_CACHE_HOME": str(cache)},
            check=True,
        )
        if source.stem == "le-tombeau-de-couperin":
            generated = [target / (source.stem + (f"-{i}" if i else "") + ".midi") for i in range(6)]
            if not all(path.is_file() for path in generated):
                raise RuntimeError("LilyPond did not produce all six movement MIDI files")
            for name, path in zip(MOVEMENTS, generated):
                path.replace(MIDI_OUT / (name + ".midi"))
            concatenate([MIDI_OUT / (name + ".midi") for name in MOVEMENTS],
                        MIDI_OUT / "le-tombeau-de-couperin.midi")
        elif target != MIDI_OUT:
            (target / (source.stem + ".midi")).replace(MIDI_OUT / (source.stem + ".midi"))
        print(f"MIDI output: {MIDI_OUT}")


if __name__ == "__main__":
    main()
