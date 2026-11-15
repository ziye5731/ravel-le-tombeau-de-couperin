#!/usr/bin/env python3
"""Check exported principal note onsets against each LilyPond MIDI movement."""
from fractions import Fraction
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'scripts'))
from midi_files import read_midi

STEPS={'C':0,'D':2,'E':4,'F':5,'G':7,'A':9,'B':11}
EXPECTED_COUNTS=[97,61,162,128,128,251]


def movements(part):
    result=[]
    for measure in part.findall('measure'):
        if measure.get('number')=='1':result.append([])
        if not result:raise ValueError('First MusicXML measure must start a movement')
        result[-1].append(measure)
    return result


def notes_by_movement(part, clarinet=False):
    result=[]
    for measures in movements(part):
        starts=[];graces=[];absolute=Fraction(0);divisions=None
        for measure in measures:
            cursor=Fraction(0);high=Fraction(0);last=cursor
            for node in measure:
                if node.tag=='attributes' and node.find('divisions') is not None:
                    divisions=int(node.findtext('divisions'))
                elif node.tag in ('backup','forward'):
                    if not divisions:raise ValueError('No MusicXML divisions')
                    amount=Fraction(int(node.findtext('duration')),divisions)
                    cursor += amount if node.tag=='forward' else -amount
                    if cursor<0:raise ValueError('MusicXML backup moved before the measure')
                elif node.tag=='note':
                    grace=node.find('grace') is not None;chord=node.find('chord') is not None
                    if not chord:last=cursor
                    pitch=node.find('pitch')
                    if pitch is not None and (grace or node.find("tie[@type='stop']") is None):
                        alter=Fraction(pitch.findtext('alter','0'))
                        if alter.denominator!=1:raise ValueError('MIDI comparison requires semitone pitches')
                        semitone=(int(pitch.findtext('octave'))+1)*12+STEPS[pitch.findtext('step')]+int(alter)
                        target=graces if grace else starts
                        target.append((absolute+last,semitone-(2 if clarinet else 0),measure.get('number')))
                    if not grace and not chord:
                        if not divisions:raise ValueError('No MusicXML divisions')
                        cursor+=Fraction(int(node.findtext('duration')),divisions)
                high=max(high,cursor)
            if high<=0:raise ValueError('MusicXML measure has no duration')
            absolute+=high
        result.append((starts,graces,absolute))
    return result


def validate(path):
    root=ET.parse(path).getroot()
    parts=root.findall('part')
    if root.tag!='score-partwise' or len(parts)!=4:raise ValueError('Expected a four-part score-partwise file')
    for part in parts:
        actual=[len(group) for group in movements(part)]
        if actual!=EXPECTED_COUNTS:raise ValueError(f'Wrong movement lengths in {part.get("id")}: {actual}')
    transposes=parts[2].findall('./measure/attributes/transpose/chromatic')
    if len(transposes)!=6 or any(t.text!='-2' for t in transposes):
        raise ValueError('B-flat clarinet transposition is missing or incorrect')
    exported=[notes_by_movement(part,clarinet=i==2) for i,part in enumerate(parts)]
    for movement in range(6):
        division,tracks=read_midi(ROOT/'tmp'/'fl-ob-cl-piano'/f'movement-{movement+1}.midi')
        for index in range(4):
            notes,graces,total=exported[index][movement]
            midi_events=[(tick,event[1]) for tick,event in tracks[index+1][0]
                         if event[0]&0xF0==0x90 and len(event)>2 and event[2]]
            midi=set(midi_events)
            expected=[(round(float(time*division)),pitch,bar) for time,pitch,bar in notes]
            # An opening grace group can shift all LilyPond MIDI events by a few ticks.
            offsets={0}
            if expected and midi_events:
                for tick,pitch,bar in expected[:16]:
                    offsets.update(t-tick for t,p in midi_events[:64]
                                   if p==pitch and 0<=t-tick<=division//8)
            best=None
            for offset in offsets:
                missing=[(tick,pitch,bar) for tick,pitch,bar in expected
                         if not any((tick+offset+delta,pitch) in midi for delta in (-1,0,1))]
                if best is None or len(missing)<len(best[0]):best=(missing,offset)
            if best and best[0]:
                raise ValueError(f'Movement {movement+1}, part {index+1}: '
                                 f'{len(best[0])} notes differ from MIDI; first {best[0][:5]}')
            offset=best[1] if best else 0
            expected_set={(tick+offset,pitch) for tick,pitch,_ in expected}
            grace_by_pitch={}
            for time,pitch,bar in graces:
                grace_by_pitch.setdefault(pitch,[]).append(round(float(time*division))+offset)
            extra=[(tick,pitch) for tick,pitch in midi_events
                   if not any((tick+delta,pitch) in expected_set for delta in (-1,0,1))
                   and not any(-80<=tick-start<=25 for start in grace_by_pitch.get(pitch,[]))]
            if extra:
                raise ValueError(f'Movement {movement+1}, part {index+1}: '
                                 f'{len(extra)} MIDI notes are absent from MusicXML; first {extra[:5]}')
        print(f'MusicXML validation: movement {movement+1}, four parts OK')


if __name__=='__main__':
    validate(Path(sys.argv[1]) if len(sys.argv)>1 else HERE/'output/score.musicxml')
