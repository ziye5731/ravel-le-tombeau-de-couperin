#!/usr/bin/env python3
"""Export the checked Prélude bars 22–29 excerpt, without claiming full-score support.

This temporary bridge uses the archived piano MusicXML for the unchanged running
piano voices and transfers the original melodic notes to the requested winds.
It refuses to run after these bars change, so it cannot silently export stale music.
"""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import re
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / 'piano/source/le-tombeau-de-couperin.musicxml'
EXPECTED = {
    'flute/01-prelude.ily': 'b1b4b9a598f0c867197a45df64aa9ea65ee090c7c55c718f72ccf29ac92594f4',
    'oboe/01-prelude.ily': 'b7d85d55fc0ef55e203a6158344591dc580d819995d26d59f9ebd2b110079ca3',
    'clarinet/01-prelude.ily': '8b33885a4914f43ed21945c1ed74e006ea8a0c8beb0e2a91a2cb038da953dbb7',
    'piano/01-prelude.ily': '0b202e3981e0e165c08a91c2668611919c7520c404c738c47efb343fd69b2a36',
}


def check_sources():
    for path, expected in EXPECTED.items():
        text = (HERE / path).read_text()
        lines = [(marker, n, line) for marker, n, line in re.findall(
            r'% (小节|measure) (\d+)\n\s*([^\n]+)', text) if 22 <= int(n) <= 29]
        if sha256(repr(lines).encode()).hexdigest() != expected:
            raise RuntimeError(f'{path} bars 22–29 changed; update the excerpt exporter before using it.')


def child(parent, tag, text=None, **attrs):
    node = ET.SubElement(parent, tag, attrs)
    if text is not None:
        node.text = str(text)
    return node


def rest(duration=1440):
    note = ET.Element('note')
    if duration == 1440:
        child(note, 'rest', measure='yes')
        child(note, 'duration', duration)
    else:
        child(note, 'rest')
        child(note, 'duration', duration)
        child(note, 'type', 'quarter')
        child(note, 'dot')
    return note


def forward(duration, voice=None, staff=None):
    node = ET.Element('forward')
    child(node, 'duration', duration)
    if voice:
        child(node, 'voice', voice)
    if staff:
        child(node, 'staff', staff)
    return node


def dynamic(parent, value):
    direction = child(parent, 'direction', placement='below')
    kind = child(direction, 'direction-type')
    dynamics = child(kind, 'dynamics')
    child(dynamics, value)


def tempo(parent):
    direction = child(parent, 'direction', placement='above')
    kind = child(direction, 'direction-type')
    metronome = child(kind, 'metronome')
    child(metronome, 'beat-unit', 'quarter')
    child(metronome, 'beat-unit-dot')
    child(metronome, 'per-minute', 92)
    child(direction, 'sound', tempo='138')


def wedge(parent, kind):
    direction = child(parent, 'direction', placement='below')
    direction_type = child(direction, 'direction-type')
    child(direction_type, 'wedge', type=kind, number='1')


def attrs(parent, *, clarinet=False, piano=False):
    a = child(parent, 'attributes')
    child(a, 'divisions', 480)
    key = child(a, 'key')
    child(key, 'fifths', 3 if clarinet else 1)
    t = child(a, 'time')
    child(t, 'beats', 12)
    child(t, 'beat-type', 16)
    if piano:
        child(a, 'staves', 2)
    clef = child(a, 'clef', **({'number': '1'} if piano else {}))
    child(clef, 'sign', 'G')
    child(clef, 'line', 2)
    if piano:
        clef = child(a, 'clef', number='2')
        child(clef, 'sign', 'F')
        child(clef, 'line', 4)
    if clarinet:
        tr = child(a, 'transpose')
        child(tr, 'diatonic', -1)
        child(tr, 'chromatic', -2)


def transpose_clarinet(note):
    pitch = note.find('pitch')
    if pitch is None:
        return
    steps = {'C': ('D', 0), 'D': ('E', 0), 'E': ('F', 1), 'F': ('G', 0),
             'G': ('A', 0), 'A': ('B', 0), 'B': ('C', 1)}
    old = pitch.findtext('step')
    new, extra = steps[old]
    pitch.find('step').text = new
    altered = int(pitch.findtext('alter', '0')) + extra
    alt = pitch.find('alter')
    if alt is not None:
        pitch.remove(alt)
    if altered:
        alt = ET.Element('alter')
        alt.text = str(altered)
        pitch.insert(1, alt)
    if old == 'B':
        pitch.find('octave').text = str(int(pitch.findtext('octave')) + 1)
    accidental = note.find('accidental')
    if accidental is not None:
        note.remove(accidental)


def no_layout(root):
    for element in root.iter():
        for name in list(element.attrib):
            if name.startswith(('default-', 'relative-')) or name in ('width', 'font-size'):
                del element.attrib[name]
        for n in list(element):
            if n.tag == 'print':
                element.remove(n)


def main():
    check_sources()
    original = ET.parse(SOURCE).getroot().find('part').findall('measure')[21:29]
    assert [m.get('number') for m in original] == [str(n) for n in range(22, 30)]
    score = ET.Element('score-partwise', version='4.0')
    work = child(score, 'work')
    child(work, 'work-title', 'Le Tombeau de Couperin - Prélude, bars 22–29 (excerpt)')
    identification = child(score, 'identification')
    child(identification, 'creator', 'Maurice Ravel', type='composer')
    plist = child(score, 'part-list')
    specs = [('P1', 'Flute', 74), ('P2', 'Oboe', 69),
             ('P3', 'Clarinet in B-flat', 72), ('P4', 'Piano', 1)]
    for index, (part_id, name, program) in enumerate(specs, 1):
        part = child(plist, 'score-part', id=part_id)
        child(part, 'part-name', name)
        inst = child(part, 'score-instrument', id=part_id+'-I1')
        child(inst, 'instrument-name', name)
        midi = child(part, 'midi-instrument', id=part_id+'-I1')
        child(midi, 'midi-channel', index)
        child(midi, 'midi-program', program)
    for part_id, name, _ in specs[:3]:
        part = child(score, 'part', id=part_id)
        for num, source in enumerate(original, 22):
            measure = child(part, 'measure', number=str(num))
            if num == 22:
                attrs(measure, clarinet=part_id == 'P3')
            if (part_id, num) in {('P3', 22), ('P2', 24),
                                  ('P1', 26), ('P2', 26), ('P3', 26),
                                  ('P1', 28), ('P2', 28), ('P3', 28)}:
                dynamic(measure, 'mp' if num == 22 else 'mf' if num == 24 else 'f' if num == 26 else 'ff')
            if num == 27:
                wedge(measure, 'crescendo')
            if num == 28:
                wedge(measure, 'stop')
            active = (part_id == 'P3' and num in (22, 23, 26, 27, 28)
                      or part_id == 'P2' and num in (24, 25, 26, 27, 28)
                      or part_id == 'P1' and num in (26, 27, 28))
            if not active:
                measure.append(rest())
                continue
            notes = [deepcopy(x) for x in source.findall('note') if x.findtext('voice') == '1']
            if num == 28:
                notes = notes[:3]
            for note in notes:
                for tag in ('staff', 'stem'):
                    node = note.find(tag)
                    if node is not None:
                        note.remove(node)
                if part_id == 'P3':
                    transpose_clarinet(note)
                measure.append(note)
            if num == 28:
                measure.append(rest(720))
    piano = child(score, 'part', id='P4')
    for num, source in enumerate(original, 22):
        measure = deepcopy(source)
        # The archive includes playback-only tempo curves and pedal data that
        # are not present in the chamber score. Avoid reintroducing them.
        for direction in list(measure.findall('direction')):
            measure.remove(direction)
        if num == 22:
            initial = ET.Element('temporary')
            attrs(initial, piano=True)
            measure.insert(0, initial[0])
            direction = ET.Element('temporary')
            tempo(direction)
            measure.insert(1, direction[0])
        if num in (22, 26, 28):
            direction = ET.Element('temporary')
            dynamic(direction, {22: 'mp', 26: 'f', 28: 'ff'}[num])
            measure.insert(2 if num == 22 else 0, direction[0])
        replaced = False
        first_half = True
        for item in list(measure):
            if item.tag == 'note' and ((num == 28 and item.findtext('voice') == '5')
                                       or (num == 29 and item.findtext('voice') == '1')):
                notations = item.find('notations')
                if notations is not None:
                    for slur in list(notations.findall('slur')):
                        notations.remove(slur)
            if item.tag == 'note' and item.findtext('voice') == '1' and num < 29:
                if num == 28 and not first_half:
                    continue
                position = list(measure).index(item)
                if not replaced:
                    measure.insert(position, forward(720 if num == 28 else 1440, '1', '1'))
                    replaced = True
                if num == 28 and item.find('grace') is None:
                    first_half = False
                measure.remove(item)
            elif item.tag == 'note' and item.get('print-object') == 'no':
                position = list(measure).index(item)
                duration = item.findtext('duration')
                if duration and item.find('chord') is None:
                    measure.insert(position, forward(int(duration), item.findtext('voice'), item.findtext('staff')))
                measure.remove(item)
        piano.append(measure)
    no_layout(score)
    ET.indent(score, space='  ')
    out = HERE / 'output/prelude-22-29.musicxml'
    ET.ElementTree(score).write(out, encoding='utf-8', xml_declaration=True)
    print(out)


if __name__ == '__main__':
    main()
