#!/usr/bin/env python3
"""Build the chamber full score and its four-instrument MIDI."""
from pathlib import Path
import os
import shutil
import struct
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "scripts"))
from midi_files import concatenate, read_midi, read_vlq, vlq

# MIDI channel volume (CC 7): keep the piano behind the three wind parts.
# This leaves the written dynamics and individual note velocities intact.
WIND_MIDI_VOLUME = 120
PIANO_MIDI_VOLUME = 45


def instrument_tracks(source, target):
    """Combine the two piano staves into one MIDI track, retaining channels."""
    division, tracks = read_midi(source)
    if len(tracks) != 6:
        raise ValueError(f"Expected conductor, flute, oboe, clarinet and two piano staves: {source}")
    def track_name(track):
        for _, event in track[0]:
            if event[:2] == b"\xff\x03":
                size, start = read_vlq(event, 2)
                return event[start:start + size].decode("utf-8")
        return ""

    by_name = {track_name(track).split(":", 1)[0]: track for track in tracks[1:]}
    if set(by_name) != {"flute", "oboe", "clarinet", "upper", "lower"}:
        raise ValueError(f"Unexpected MIDI instrument tracks in {source}: {list(by_name)}")
    # LilyPond may assign channels in a different order in each movement.
    # Keep them stable so the combined file remains editable as four parts.
    for name, channel in {"flute": 0, "oboe": 1, "clarinet": 2, "upper": 3, "lower": 4}.items():
        events, end = by_name[name]
        events = [(tick, bytes([(event[0] & 0xF0) | channel]) + event[1:]
                   if 0x80 <= event[0] < 0xF0 else event)
                  for tick, event in events]
        volume = PIANO_MIDI_VOLUME if name in {"upper", "lower"} else WIND_MIDI_VOLUME
        events.insert(0, (0, bytes([0xB0 | channel, 7, volume])))
        by_name[name] = (events, end)
    piano = [by_name["upper"], by_name["lower"]]
    piano_events = sorted(
        [event for part, _ in piano for event in part if event[1][:2] != b"\xff\x03"],
        key=lambda event: event[0],
    )
    piano_events.insert(0, (0, b"\xff\x03\x05Piano"))
    combined = [tracks[0], by_name["flute"], by_name["oboe"], by_name["clarinet"],
                (piano_events, max(end for _, end in piano))]
    data = b"MThd" + struct.pack(">IHHH", 6, 1, len(combined), division)
    for events, end in combined:
        body = bytearray()
        previous = 0
        for tick, event in events:
            body.extend(vlq(tick - previous) + event)
            previous = tick
        body.extend(vlq(end - previous) + b"\xff\x2f\x00")
        data += b"MTrk" + struct.pack(">I", len(body)) + body
    target.write_bytes(data)


def main():
    lilypond = shutil.which("lilypond")
    if not lilypond:
        sys.exit("LilyPond is required (tested with 2.26.0).")
    stage = ROOT / "tmp" / "fl-ob-cl-piano"
    stage.mkdir(parents=True, exist_ok=True)
    output = HERE / "output"
    output.mkdir(exist_ok=True)
    cache = ROOT / "tmp" / "cache"
    cache.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [lilypond, "-dno-point-and-click", "-o", str(stage / "suite"), str(HERE / "score.ly")],
        cwd=HERE,
        env={**os.environ, "XDG_CACHE_HOME": str(cache)},
        check=True,
    )
    movements = []
    for i in range(6):
        original = stage / ("suite" + (f"-{i}" if i else "") + ".midi")
        processed = stage / f"movement-{i + 1}.midi"
        instrument_tracks(original, processed)
        movements.append(processed)
    concatenate(movements, output / "score.midi")
    shutil.copyfile(stage / "suite.pdf", output / "score.pdf")
    print(f"Full score: {output / 'score.pdf'}")
    print(f"MIDI: {output / 'score.midi'}")


if __name__ == "__main__":
    main()
