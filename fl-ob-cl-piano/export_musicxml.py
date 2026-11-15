#!/usr/bin/env python3
"""Export the compiler-resolved four-instrument LilyPond score to MusicXML.

LilyPond expands includes, pitch transposition and Scheme before conversion.
Requires python-ly's xml-export.ily and LilyPond 2.26.
"""
from __future__ import annotations
import argparse
from collections import Counter
from fractions import Fraction
from importlib.resources import files
from pathlib import Path
import json
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DIV = 6720  # divisible by the score's seven-note tuplets
WHOLE = DIV * 4
TYPES = {-2:'breve', -1:'breve', 0:'whole', 1:'half', 2:'quarter', 3:'eighth', 4:'16th', 5:'32nd', 6:'64th', 7:'128th', 8:'256th'}
STEPS = 'CDEFGAB'
TITLES = ['I. PRÉLUDE', 'II. FUGUE', 'III. FORLANE', 'IV. RIGAUDON', 'V. MENUET', 'VI. TOCCATA']


def sub(e, tag, text=None, **attrs):
    n = ET.SubElement(e, tag, {k: str(v) for k,v in attrs.items()})
    if text is not None: n.text = str(text)
    return n


def extract():
    try:
        export = Path(str(files('ly.xml').joinpath('xml-export.ily')))
    except (ModuleNotFoundError, FileNotFoundError) as exc:
        raise RuntimeError('MusicXML export requires python-ly; install requirements-musicxml.txt') from exc
    lilypond = shutil.which('lilypond')
    if not lilypond: raise RuntimeError('LilyPond is required')
    stage = ROOT / 'tmp' / 'fl-ob-cl-piano'
    stage.mkdir(parents=True, exist_ok=True)
    dest = stage / 'music-tree.xml'
    wrapper = stage / 'extract-music.ly'
    def quoted(p): return json.dumps(str(p.resolve()), ensure_ascii=False)
    # The wrapper follows the MIT-licensed ly-to-musicxml extraction approach:
    # https://github.com/xvb8/ly-to-musicxml
    wrapper.write_text(r'''\version "2.26.0"
#(ly:set-option 'relative-includes #t)
\include EXPORT
#(define xml-outputter
   (let* ((port (open-output-file OUTPUT)) (xml (XML port)))
     (xml 'declaration) (xml 'open-tag 'document) xml))
#(define-public (xml-book-handler book) (obj->lily-xml book xml-outputter))
#(ly:parser-define! 'toplevel-book-handler xml-book-handler)
\include SCORE
#(if (pair? toplevel-bookparts)
    (let ((book (ly:make-book $defaultpaper $defaultheader)))
      (for-each (lambda (part) (ly:book-add-bookpart! book part))
                (reverse! toplevel-bookparts))
      (set! toplevel-bookparts (list))
      (xml-book-handler book)))
#(xml-outputter 'close-tag)
'''.replace('EXPORT',quoted(export)).replace('OUTPUT',quoted(dest)).replace('SCORE',quoted(HERE/'score.ly')))
    result = subprocess.run([lilypond, '-dno-print-pages', str(wrapper)], cwd=HERE, text=True, capture_output=True)
    if result.returncode or not dest.exists():
        raise RuntimeError('LilyPond music extraction failed:\n' + result.stderr[-6000:])
    root = ET.parse(dest).getroot()
    scores = root.findall('./book/book/score')
    if len(scores) != 6: raise RuntimeError(f'Expected 6 movements; found {len(scores)}')
    return scores


def prop(e, name, tag='number'):
    return e.findtext(f"property[@name='{name}']/{tag}")


def children(e):
    return list(e.findall('./element/music')) + list(e.findall('./elements/music'))


def context_id(e):
    return prop(e,'context-id','string')


def context_type(e):
    return prop(e,'context-type','symbol')


def staves(e):
    if e.tag == 'music' and e.get('name') == 'ContextSpeccedMusic' and context_type(e) == 'Staff' and context_id(e):
        return [e]
    return [item for node in e for item in staves(node)]


def ticks(e):
    m = e.find("property[@name='length']/moment")
    if m is None: return 0
    value = Fraction(int(m.get('main-numer')), int(m.get('main-denom'))) * WHOLE
    if value.denominator != 1: raise ValueError(f'Nonintegral duration {value}')
    return int(value)


def dynamic(value, staff=None):
    d = ET.Element('direction', placement='below'); typ=sub(d,'direction-type'); dy=sub(typ,'dynamics');sub(dy,value)
    if staff: sub(d,'staff',staff)
    return d


def wedge(kind, staff=None):
    d=ET.Element('direction',placement='below');ty=sub(d,'direction-type');sub(ty,'wedge',type=kind,number='1')
    if staff:sub(d,'staff',staff)
    return d


def tempo(e, staff=None):
    d=ET.Element('direction',placement='above');typ=sub(d,'direction-type')
    label=prop(e,'text','string')
    if label:sub(typ,'words',label)
    unit=e.find("property[@name='tempo-unit']/duration")
    number=prop(e,'metronome-count')
    if unit is not None and number:
        typ=sub(d,'direction-type'); metro=sub(typ,'metronome');sub(metro,'beat-unit',TYPES[int(unit.get('log'))])
        for _ in range(int(unit.get('dots','0'))): sub(metro,'beat-unit-dot')
        sub(metro,'per-minute',number)
        length=Fraction(1,2**int(unit.get('log'))) * sum((Fraction(1,2**n) for n in range(int(unit.get('dots','0'))+1)),Fraction(0))
    if staff:sub(d,'staff',staff)
    if unit is not None and number:sub(d,'sound',tempo=str(float(Fraction(number)*length*4)))
    return d


def key(e):
    alist=e.find("property[@name='pitch-alist']/list")
    if alist is None: return None
    values=[Fraction(pair.findall('number')[1].text) for pair in alist.findall('pair') if len(pair.findall('number'))==2]
    if any(v>0 for v in values) and any(v<0 for v in values):raise ValueError('Mixed accidentals in key signature')
    return sum(1 if v>0 else -1 if v<0 else 0 for v in values)


def make_attributes(*, divisions=False, fifths=None, beats=None, beat_type=None, piano=False, clarinet=False, clef=None):
    a=ET.Element('attributes')
    if divisions:sub(a,'divisions',DIV)
    if fifths is not None:k=sub(a,'key');sub(k,'fifths',fifths)
    if beats is not None:
        t=sub(a,'time');sub(t,'beats',beats);sub(t,'beat-type',beat_type)
    if piano and divisions:sub(a,'staves',2)
    if divisions:
        for number, sign, line in ([(1,'G',2),(2,'F',4)] if piano else [(None,'G',2)]):
            c=sub(a,'clef',**({'number':number} if number else {}));sub(c,'sign',sign);sub(c,'line',line)
    if clef:
        number,sign,line=clef;c=sub(a,'clef',number=number);sub(c,'sign',sign);sub(c,'line',line)
    if clarinet and divisions:
        tr=sub(a,'transpose');sub(tr,'diatonic',-1);sub(tr,'chromatic',-2)
    return a


def parsed_direction(attachment, staff):
    name=attachment.get('name')
    if name=='AbsoluteDynamicEvent':
        value=prop(attachment,'text','string')
        if value and re.fullmatch(r'p{1,6}|f{1,6}|m[pf]|sfz|sffz|fp|sf|sfp|rfz',value):return dynamic(value,staff)
    if name in ('CrescendoEvent','DecrescendoEvent'):
        span=prop(attachment,'span-direction')
        return wedge('stop' if span=='1' else 'crescendo' if name=='CrescendoEvent' else 'diminuendo',staff)
    if name=='TextScriptEvent':
        strings=[n.text for n in attachment.findall(".//property[@name='text']//string") if n.text]
        if strings:
            d=ET.Element('direction',placement='above');typ=sub(d,'direction-type')
            text=' '.join(strings)
            if text.startswith('Juillet 1914'):
                text=text.replace(' - Juin, Novembre',' -\nJuin, Novembre')
                sub(typ,'words',text,justify='right',halign='right')
            else:sub(typ,'words',text)
            if staff:sub(d,'staff',staff)
            return d
    if name=='SustainEvent':
        direction=prop(attachment,'span-direction')
        d=ET.Element('direction',placement='below');typ=sub(d,'direction-type')
        sub(typ,'pedal',type='start' if direction=='-1' else 'stop',line='yes')
        if staff:sub(d,'staff',staff)
        return d
    return None


def attachments(node):
    return list(node.findall('./articulations/music'))


class VoiceReader:
    def __init__(self, staff, voice, is_piano):
        self.staff=staff;self.voice=voice;self.is_piano=is_piano
        self.bars=[[]];self.lengths=[0];self.active_ties=set();self.unknown=Counter()
        self.clef_glyph=None;self.volta=None;self.octaves={}
    def emit(self, e):self.bars[-1].append(e)
    def advance(self,duration):self.lengths[-1]+=duration
    def directions(self, aa):
        for a in aa:
            d=parsed_direction(a,self.staff if self.is_piano else None)
            if d is not None:self.emit(d)
    def note_group(self, nodes, aa, grace):
        if not nodes:return
        duration=ticks(nodes[0]); self.directions(attachments(nodes[0])+aa)
        for index,src in enumerate(nodes):
            n=ET.Element('note')
            if grace:sub(n,'grace')
            if index:sub(n,'chord')
            pitch=src.find('pitch')
            if pitch is None:sub(n,'rest')
            else:
                p=sub(n,'pitch');sub(p,'step',STEPS[int(pitch.get('notename'))])
                altered=Fraction(pitch.get('alteration','0'))*2
                if altered:sub(p,'alter',str(altered))
                sub(p,'octave',int(pitch.get('octave'))+4)
            if not grace:sub(n,'duration',duration)
            pitch_key=(pitch.get('octave'),pitch.get('notename'),pitch.get('alteration')) if pitch is not None else None
            start=any(x.get('name')=='TieEvent' for x in attachments(src)+aa)
            stop=pitch_key in self.active_ties
            if stop:sub(n,'tie',type='stop')
            if start:sub(n,'tie',type='start')
            if pitch_key is not None:
                if start:self.active_ties.add(pitch_key)
                elif stop:self.active_ties.discard(pitch_key)
            sub(n,'voice',self.voice)
            duration_el=src.find('duration')
            if duration_el is not None:
                log=int(duration_el.get('log','2'));sub(n,'type',TYPES.get(log,'quarter'))
                for _ in range(int(duration_el.get('dots','0'))):sub(n,'dot')
                ratio=Fraction(duration_el.get('numer','1'))/Fraction(duration_el.get('denom','1'))
                if ratio!=1 and not grace:
                    tm=sub(n,'time-modification');sub(tm,'actual-notes',ratio.denominator);sub(tm,'normal-notes',ratio.numerator)
            if self.is_piano:sub(n,'staff',self.staff)
            allatt=attachments(src)+(aa if index==0 else [])
            notations=None
            def nt():
                nonlocal notations
                if notations is None:notations=sub(n,'notations')
                return notations
            if stop:sub(nt(),'tied',type='stop')
            if start:sub(nt(),'tied',type='start')
            for a in allatt:
                typ=a.get('name')
                if typ=='SlurEvent':
                    direction=prop(a,'span-direction');ident=prop(a,'spanner-id') or '1'
                    sub(nt(),'slur',type='start' if direction=='-1' else 'stop',number=ident)
                elif typ=='ArticulationEvent':
                    art=prop(a,'articulation-type','symbol')
                    if art in ('accent','staccato','tenuto','staccatissimo','strong-accent'):
                        arts=nt().find('articulations')
                        if arts is None:arts=sub(nt(),'articulations')
                        sub(arts,art)
                    elif art=='portato':
                        arts=nt().find('articulations')
                        if arts is None:arts=sub(nt(),'articulations')
                        sub(arts,'detached-legato')
                    elif art=='trill':
                        ornaments=nt().find('ornaments')
                        if ornaments is None:ornaments=sub(nt(),'ornaments')
                        sub(ornaments,'trill-mark')
                    elif art=='fermata':sub(nt(),'fermata')
            self.emit(n)
        if not grace:self.advance(duration)
    def visit(self, e, grace=False):
        name=e.get('name')
        if name=='BarCheckEvent':
            if grace: raise ValueError('Barcheck inside grace')
            self.bars.append([]);self.lengths.append(0);return
        # InitialContextMusic in LilyPond's grace wrapper contains a second
        # copy of the grace notes used to initialise context, not extra notes.
        if name=='InitialContextMusic':return
        if name in ('SequentialMusic','ContextSpeccedMusic','TransposedMusic'):
            for x in children(e):self.visit(x,grace)
            return
        if name=='GraceMusic':
            for x in children(e):self.visit(x,True)
            return
        if name=='TremoloRepeatedMusic':
            start=len(self.bars[-1]);before=self.lengths[-1]
            for x in children(e):self.visit(x,grace)
            emitted=self.bars[-1][start:]
            groups=[]
            for n in emitted:
                if n.tag=='note':
                    if n.find('chord') is None:groups.append([])
                    groups[-1].append(n)
            if len(groups)!=2:raise ValueError('Expected two note groups in a tremolo')
            total=ticks(e);half=total//2
            if total%2:raise ValueError('Tremolo duration is not divisible in two')
            length=Fraction(total,WHOLE)
            notation={Fraction(3,4):('half',1,1),Fraction(3,8):('quarter',1,2)}.get(length)
            if notation is None:raise ValueError(f'Unsupported tremolo length {length}')
            typename,dots,base_log=notation
            source_note=next(x for x in e.iter('music') if x.get('name')=='NoteEvent')
            marks=int(source_note.find('duration').get('log'))-base_log
            for gi,group in enumerate(groups):
                for n in group:
                    n.find('duration').text=str(half)
                    typ=n.find('type');typ.text=typename
                    for dot in list(n.findall('dot')):n.remove(dot)
                    pos=list(n).index(typ)+1
                    for _ in range(dots):n.insert(pos,ET.Element('dot'));pos+=1
                    tm=n.find('time-modification')
                    if tm is not None:n.remove(tm)
                    tm=ET.Element('time-modification');sub(tm,'actual-notes',2);sub(tm,'normal-notes',1)
                    staff=n.find('staff');n.insert(list(n).index(staff) if staff is not None else len(n),tm)
                first=group[0];notations=first.find('notations')
                if notations is None:notations=sub(first,'notations')
                ornaments=notations.find('ornaments')
                if ornaments is None:ornaments=sub(notations,'ornaments')
                sub(ornaments,'tremolo',marks,type='start' if gi==0 else 'stop')
            self.lengths[-1]=before+total
            return
        if name=='EventChord':
            es=e.findall('./elements/music');notes=[x for x in es if x.get('name')=='NoteEvent'];aa=[x for x in es if x.get('name')!='NoteEvent']
            self.note_group(notes,aa,grace);return
        if name=='NoteEvent':self.note_group([e],[],grace);return
        if name in ('RestEvent','MultiMeasureRestMusic'):
            self.directions(attachments(e));duration=ticks(e)
            n=ET.Element('note');sub(n,'rest',**({'measure':'yes'} if name=='MultiMeasureRestMusic' else {}))
            if not grace:sub(n,'duration',duration)
            sub(n,'voice',self.voice)
            d=e.find('duration')
            if d is not None and name!='MultiMeasureRestMusic':
                sub(n,'type',TYPES.get(int(d.get('log','2')),'quarter'))
                for _ in range(int(d.get('dots','0'))):sub(n,'dot')
            if self.is_piano:sub(n,'staff',self.staff)
            for a in attachments(e):
                if a.get('name')=='SlurEvent':
                    notations=n.find('notations')
                    if notations is None:notations=sub(n,'notations')
                    sub(notations,'slur',type='start' if prop(a,'span-direction')=='-1' else 'stop',number=prop(a,'spanner-id') or '1')
            self.emit(n)
            if not grace:self.advance(duration)
            return
        if name=='SkipEvent':
            self.directions(attachments(e));duration=ticks(e)
            if duration:
                f=ET.Element('forward');sub(f,'duration',duration);sub(f,'voice',self.voice)
                if self.is_piano:sub(f,'staff',self.staff)
                self.emit(f);self.advance(duration)
            return
        if name=='ContextChange':
            target=prop(e,'change-to-id','string')
            if target in ('upper','lower'):self.staff='1' if target=='upper' else '2'
            return
        if name=='PropertySet':
            symbol=prop(e,'symbol','symbol')
            if symbol=='clefGlyph':self.clef_glyph=prop(e,'value','string')
            if symbol=='repeatCommands':
                for item in e.findall("property[@name='value']/list/list"):
                    if item.findtext('symbol')!='volta':continue
                    label=item.findtext('string')
                    if label:
                        self.volta=re.sub(r'[^0-9,]','',label) or label
                        barline=ET.Element('barline',location='left')
                        sub(barline,'ending',number=self.volta,type='start');self.emit(barline)
                    elif item.findtext('boolean')=='false' and self.volta:
                        barline=ET.Element('barline',location='right')
                        sub(barline,'ending',number=self.volta,type='stop')
                        if not self.lengths[-1] and len(self.bars)>1:self.bars[-2].append(barline)
                        else:self.emit(barline)
                        self.volta=None
            return
        if name=='ApplyContext':
            glyph=self.clef_glyph
            if self.is_piano and glyph in ('clefs.G','clefs.F','clefs.C'):
                sign=glyph[-1];self.emit(make_attributes(clef=(self.staff,sign,{'G':2,'F':4,'C':3}[sign])))
            self.clef_glyph=None
            return
        if name=='OttavaEvent':
            number=int(prop(e,'ottava-number') or 0)
            if number==0 and not self.octaves.get(self.staff):return
            if number:self.octaves[self.staff]=number
            else:self.octaves.pop(self.staff,None)
            d=ET.Element('direction',placement='above' if number>=0 else 'below');typ=sub(d,'direction-type')
            sub(typ,'octave-shift',type='stop' if number==0 else 'down' if number>0 else 'up',
                size=str(7*abs(number)+1 if number else 8),number=self.staff if self.is_piano else '1')
            if self.is_piano:sub(d,'staff',self.staff)
            self.emit(d);return
        if name=='KeyChangeEvent':
            fifths=key(e)
            if fifths is not None:self.emit(make_attributes(fifths=fifths))
            return
        if name=='ReferenceTimeSignatureMusic':
            pair=e.find("property[@name='time-signature']/pair")
            if pair is not None:
                nums=[x.text for x in pair.findall('number')]
                if len(nums)==2:self.emit(make_attributes(beats=nums[0],beat_type=nums[1]))
            return
        if name=='TempoChangeEvent':self.emit(tempo(e,self.staff if self.is_piano else None));return
        if name in ('AbsoluteDynamicEvent','CrescendoEvent','DecrescendoEvent'):
            d=parsed_direction(e,self.staff if self.is_piano else None)
            if d is not None:self.emit(d)
            return
        if name=='BarEvent':
            style=prop(e,'bar-type','string')
            if style in ('.|:',':|.','||','|.'):
                b=ET.Element('barline',location='left' if style=='.|:' else 'right')
                if style in ('.|:',':|.'):sub(b,'repeat',direction='forward' if style=='.|:' else 'backward')
                else:sub(b,'bar-style','light-light' if style=='||' else 'light-heavy')
                self.emit(b)
            return
        if name in ('TextScriptEvent','SustainEvent'):
            d=parsed_direction(e,self.staff if self.is_piano else None)
            if d is not None:self.emit(d)
            return
        if name=='BreathingEvent':
            note=next((x for x in reversed(self.bars[-1]) if x.tag=='note'),None)
            if note is None:raise ValueError('Breath mark has no preceding note')
            notations=note.find('notations')
            if notations is None:notations=sub(note,'notations')
            arts=notations.find('articulations')
            if arts is None:arts=sub(notations,'articulations')
            sub(arts,'breath-mark')
            return
        if name in ('OverrideProperty','RevertProperty','BarNumberCheck'):
            return
        if name=='SimultaneousMusic':raise ValueError(f'Unexpected nested simultaneous music in voice {self.voice}')
        self.unknown[name]+=1
    def finish(self):
        if len(self.bars)>1 and self.lengths[-1]==0:
            self.bars[-2].extend(self.bars[-1]);self.bars.pop();self.lengths.pop()
        if self.unknown:raise ValueError(f'Unsupported music nodes in voice {self.voice}: {self.unknown}')
        return self


def read_staff(staff, is_piano):
    if not is_piano:
        vr=VoiceReader('1','1',False);vr.visit(staff);return [vr.finish()]
    sim=next((e for e in staff.iter('music') if e.get('name')=='SimultaneousMusic'),None)
    if sim is None:raise ValueError('Piano staff missing simultaneous voices')
    result=[];initial='1' if context_id(staff)=='upper' else '2'
    for voice in sim.findall('./elements/music'):
        ident=context_id(voice)
        reader=VoiceReader(initial,ident[1:] if ident else ('90' if initial=='1' else '91'),True)
        reader.visit(voice);result.append(reader.finish())
    return result


def move_groups(lengths, movement):
    groups=[[i] for i in range(len(lengths))]
    if movement==2:
        assert lengths[139:141] == [WHOLE*3//8,WHOLE*3//8]
        groups[139:141]=[[139,140]]
    return groups


def verify_lengths(readers, count, movement):
    for reader in readers:
        if len(reader.bars)!=count:raise ValueError(f'Movement {movement+1}, voice {reader.voice}: expected {count} bars, got {len(reader.bars)}')
    for i in range(count):
        expected=max(r.lengths[i] for r in readers)
        for reader in readers:
            if reader.lengths[i]!=expected:raise ValueError(f'Movement {movement+1}, bar {i+1}, voice {reader.voice}: {reader.lengths[i]} vs {expected}')


def main(output=None):
    scores=extract();allparts=[[],[],[],[]]
    expected_counts=[97,61,163,128,128,251]
    for mov,score in enumerate(scores):
        found=staves(score);byid={context_id(x):x for x in found}
        if set(byid)!={'flute','oboe','clarinet','upper','lower'}:raise ValueError(f'Unexpected staves in movement {mov+1}: {list(byid)}')
        p=[read_staff(byid[x],False) for x in ('flute','oboe','clarinet')]
        p.append(read_staff(byid['upper'],True)+read_staff(byid['lower'],True))
        every=[x for group in p for x in group];verify_lengths(every,expected_counts[mov],mov)
        groups=move_groups(every[0].lengths,mov)
        movement_tempo=next((el for reader in p[3] for el in reader.bars[0]
                             if el.tag=='direction' and el.find('./direction-type/metronome') is not None),None)
        for part_index,readers in enumerate(p):
            for measure_index,group in enumerate(groups):
                m=ET.Element('measure',number=str(measure_index+1))
                if measure_index==0:
                    if mov:sub(m,'print',**{'new-system':'yes'})
                    m.append(make_attributes(divisions=True,piano=part_index==3,clarinet=part_index==2))
                    if part_index==0:
                        d=sub(m,'direction',placement='above');ty=sub(d,'direction-type');sub(ty,'words',TITLES[mov])
                        if movement_tempo is not None:
                            import copy
                            t=copy.deepcopy(movement_tempo)
                            staff=t.find('staff')
                            if staff is not None:t.remove(staff)
                            m.append(t)
                wholebar=sum(readers[0].lengths[i] for i in group)
                barlines=[]
                for reader in readers:
                    for bar in group:
                        barlines.extend(el for el in reader.bars[bar] if el.tag=='barline')
                def merged_barline(location):
                    matching=[x for x in barlines if x.get('location')==location]
                    if not matching:return None
                    merged=ET.Element('barline',location=location)
                    for tag in ('bar-style','ending','repeat'):
                        child=next((x.find(tag) for x in matching if x.find(tag) is not None),None)
                        if child is not None:merged.append(child)
                    return merged
                left=merged_barline('left')
                if left is not None:m.append(left)
                for vi,reader in enumerate(readers):
                    if vi:
                        backup=sub(m,'backup');sub(backup,'duration',wholebar)
                    for bar in group:
                        for el in reader.bars[bar]:
                            if el.tag!='barline' and el is not movement_tempo:m.append(el)
                right=merged_barline('right')
                if right is not None:m.append(right)
                allparts[part_index].append(m)
        print('MusicXML:',TITLES[mov],len(groups),'bars',flush=True)
    root=ET.Element('score-partwise',version='4.0')
    work=sub(root,'work');sub(work,'work-title','Le Tombeau de Couperin')
    ident=sub(root,'identification');sub(ident,'creator','Maurice Ravel',type='composer')
    encoding=sub(ident,'encoding');sub(encoding,'software','LilyPond compiler-based MusicXML export')
    plist=sub(root,'part-list')
    specs=[('P1','Flûte',74),('P2','Hautbois',69),('P3','Clarinette en Si♭',72),('P4','Piano',1)]
    for i,(pid,name,program) in enumerate(specs,1):
        p=sub(plist,'score-part',id=pid);sub(p,'part-name',name)
        si=sub(p,'score-instrument',id=pid+'-I1');sub(si,'instrument-name',name)
        mi=sub(p,'midi-instrument',id=pid+'-I1');sub(mi,'midi-channel',i);sub(mi,'midi-program',program)
        sub(mi,'volume','35.43' if pid=='P4' else '94.49')
    for (pid,_,_),measures in zip(specs,allparts):
        part=sub(root,'part',id=pid);part.extend(measures)
    output=Path(output) if output is not None else HERE/'output/score.musicxml'
    output.parent.mkdir(parents=True,exist_ok=True)
    ET.indent(root,space='  ');ET.ElementTree(root).write(output,encoding='utf-8',xml_declaration=True)
    print('MusicXML full score:',output)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,help='Output path (default: output/score.musicxml)')
    main(parser.parse_args().output)
