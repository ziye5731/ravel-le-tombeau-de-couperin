#!/usr/bin/env python3
"""Check LilyPond's parsed note counts and exact voice durations."""
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "piano/lilypond"
LENGTHS = ["291/4", "61", "243/2", "64", "96", "251/2"]
WORDS = ["Zero", "One", "Two", "Three", "Four", "Five", "Six", "Seven"]


def main():
    reports = json.loads((BASE / "import-report.json").read_text())
    lines = [r'\version "2.26.0"', r'''
#(define (printed-note-count music)
   (let ((name (ly:music-property music 'name))
         (child (ly:music-property music 'element))
         (children (ly:music-property music 'elements)))
     ;; LilyPond 2.26 stores an initial-context copy of grace notes.
     (if (eq? name 'InitialContextMusic) 0
         (+ (if (eq? name 'NoteEvent) 1 0)
            (if (ly:music? child) (printed-note-count child) 0)
            (apply + (map printed-note-count children))))))
''']
    for report, length in zip(reports, LENGTHS):
        name = report["movement"]
        prefix = name.split("-")[1]
        lines.append(r'\include "' + str(BASE / "movements" / (name + ".ily")) + '"')
        voices = [prefix + "Voice" + WORDS[int(v)] for v in report["voices"]]
        count = "(+ " + " ".join("(printed-note-count " + v + ")" for v in voices) + ")"
        lines.append(f'#(if (not (= {count} {report["visible_pitches"]})) '
                     f'(ly:error "Note count mismatch: {name}"))')
        for voice in voices:
            lines.append(f'#(if (not (equal? (ly:music-length {voice}) '
                         f'(ly:make-moment {length}))) '
                         f'(ly:error "Voice duration mismatch: {voice}"))')
        lines.append(f'#(ly:message "Validated {name}: {report["visible_pitches"]} notes")')
    path = ROOT / "tmp/validate-music.ly"
    path.parent.mkdir(exist_ok=True)
    path.write_text("\n".join(lines) + "\n")
    subprocess.run(["lilypond", "-dno-print-pages", str(path)], check=True)


if __name__ == "__main__":
    main()
