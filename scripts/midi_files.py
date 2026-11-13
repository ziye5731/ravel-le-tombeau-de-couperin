"""Concatenate LilyPond SMF files, preserving tempo maps and all track events."""
from pathlib import Path
import struct


def read_vlq(data, pos):
    value = 0
    for _ in range(4):
        byte = data[pos]
        pos += 1
        value = (value << 7) | (byte & 127)
        if byte < 128:
            return value, pos
    raise ValueError("Invalid MIDI variable-length quantity")


def vlq(value):
    result = [value & 127]
    value >>= 7
    while value:
        result.insert(0, (value & 127) | 128)
        value >>= 7
    return bytes(result)


def read_midi(path):
    data = Path(path).read_bytes()
    if data[:4] != b"MThd":
        raise ValueError(f"Not a MIDI file: {path}")
    header_length = struct.unpack_from(">I", data, 4)[0]
    format_id, count, division = struct.unpack_from(">HHH", data, 8)
    if format_id not in (0, 1) or division & 0x8000:
        raise ValueError("Expected synchronous MIDI with metrical timing")
    pos = 8 + header_length
    tracks = []
    for _ in range(count):
        if data[pos:pos + 4] != b"MTrk":
            raise ValueError("Missing MIDI track")
        length = struct.unpack_from(">I", data, pos + 4)[0]
        track = data[pos + 8:pos + 8 + length]
        pos += 8 + length
        events, tick, offset, running = [], 0, 0, None
        while offset < len(track):
            delta, offset = read_vlq(track, offset)
            tick += delta
            status = track[offset]
            if status >= 128:
                offset += 1
            else:
                if running is None:
                    raise ValueError("Missing MIDI running status")
                status = running
            if status == 0xFF:
                kind = track[offset]
                offset += 1
                size, offset = read_vlq(track, offset)
                payload = track[offset:offset + size]
                offset += size
                running = None
                if kind != 0x2F:  # Write one final end-of-track after concatenation.
                    events.append((tick, bytes([status, kind]) + vlq(size) + payload))
            elif status in (0xF0, 0xF7):
                size, offset = read_vlq(track, offset)
                payload = track[offset:offset + size]
                offset += size
                running = None
                events.append((tick, bytes([status]) + vlq(size) + payload))
            elif status < 0xF0:
                size = 1 if status >> 4 in (0xC, 0xD) else 2
                events.append((tick, bytes([status]) + track[offset:offset + size]))
                offset += size
                running = status
            else:
                raise ValueError(f"Unsupported MIDI event: {status:#x}")
        tracks.append((events, tick))
    if pos != len(data):
        raise ValueError("Unexpected trailing MIDI data")
    return division, tracks


def concatenate(paths, output):
    """Reuse corresponding tracks, shifting each movement by its full duration."""
    division, tracks, offset = None, [], 0
    for path in paths:
        current_division, source_tracks = read_midi(path)
        if division is None:
            division = current_division
        if current_division != division:
            raise ValueError("MIDI files have different tick resolutions")
        while len(tracks) < len(source_tracks):
            tracks.append([])
        for target, (events, _) in zip(tracks, source_tracks):
            target.extend((tick + offset, event) for tick, event in events)
        offset += max(end for _, end in source_tracks)
    data = b"MThd" + struct.pack(">IHHH", 6, 1, len(tracks), division)
    for events in tracks:
        body, previous = bytearray(), 0
        for tick, event in events:
            body.extend(vlq(tick - previous) + event)
            previous = tick
        body.extend(vlq(offset - previous) + b"\xff\x2f\x00")
        data += b"MTrk" + struct.pack(">I", len(body)) + body
    Path(output).write_bytes(data)
