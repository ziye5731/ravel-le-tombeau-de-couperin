#!/usr/bin/env python3
"""Regenerate editable LilyPond voices from the archived MusicXML working source.

Timing is reconstructed measure by measure. Nonprinting playback notes become
skips, so performance-only material never appears in the engraved edition.
The generated .ily files are the editable score; rebuilding the PDF does not
run this importer or overwrite editorial work.
"""
from pathlib import Path
from fractions import Fraction as F
from collections import defaultdict, Counter
import xml.etree.ElementTree as E
import json

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'piano/lilypond'
NAMES=['01-prelude','02-fugue','03-forlane','04-rigaudon','05-menuet','06-toccata']
TITLES=['I. PRÉLUDE','II. FUGUE','III. FORLANE','IV. RIGAUDON','V. MENUET','VI. TOCCATA']
DEDICATIONS=['du lieutenant Jacques Charlot','du sous-lieutenant Jean Cruppi','du lieutenant Gabriel Deluc','de Pierre et Pascal Gaudin','de Jean Dreyfus','du capitaine Joseph de Marliave']
TEMPOS=[('Vif','4.',92),('Allegro moderato','4',84),('Allegretto','4.',92),('Assez vif','4',138),('Allegro moderato','4',92),('Vif','4',144)]
PAGE_STARTS=[[18,37,56,75],[22,42],[25,55,84,114,142],[31,69,99],[33,73,103],[26,57,86,115,144,173,203,232]]
KEYS={-7:'ces',-6:'ges',-5:'des',-4:'aes',-3:'ees',-2:'bes',-1:'f',0:'c',1:'g',2:'d',3:'a',4:'e',5:'b',6:'fis',7:'cis'}
TYPES={'whole':'1','half':'2','quarter':'4','eighth':'8','16th':'16','32nd':'32','64th':'64','128th':'128','256th':'256'}
STAFF={'1':'upper','2':'lower'}

def quote(s):return '"'+s.replace('\\','\\\\').replace('"','\\"').replace('\n',' ')+'"'
def skip(d):return 's1*'+str(d.numerator)+'/'+str(d.denominator) if d else ''
def duration(n,d):
 t=TYPES.get(n.findtext('type'))
 if t:
  t+='.'*len(n.findall('dot'))
  tm=n.find('time-modification')
  if tm is not None:t+='*'+tm.findtext('normal-notes')+'/'+tm.findtext('actual-notes')
  return t
 return '1*'+str(d.numerator)+'/'+str(d.denominator)
def pitch(n):
 p=n.find('pitch');step=p.findtext('step').lower();a=F(p.findtext('alter','0'));octave=int(p.findtext('octave'))
 accidental={F(-2):'eses',F(-1):'es',F(0):'',F(1):'is',F(2):'isis'}[a]
 suffix="'"*(octave-3) if octave>=3 else ','*(3-octave)
 forced='!' if n.find('accidental') is not None else ''
 return step+accidental+suffix+forced

def movements(root):
 ms=root.find('part').findall('measure');starts=[i for i,m in enumerate(ms) if m.get('number')=='1']+[len(ms)]
 return [ms[a:b] for a,b in zip(starts,starts[1:])]

def parse(ms,index,primary=True):
 bars=[];div=480;beats,unit=[(12,16),(4,4),(6,8),(2,4),(3,4),(2,4)][index]
 clefs={'1':'treble','2':('bass' if index in [2,3] else 'treble')};key=0 if index==3 else 1
 for mi,m in enumerate(ms):
  attrs=m.find('attributes')
  if attrs is not None:
   div=int(attrs.findtext('divisions',str(div)))
   key=int(attrs.findtext('key/fifths',str(key)))
   if attrs.find('time') is not None:beats=int(attrs.findtext('time/beats'));unit=int(attrs.findtext('time/beat-type'))
  length=F(beats,unit)
  if primary and index==2 and m.get('number') in ['140','X1']:length=F(3,8)
  shift=F(1,8) if primary and index==3 and m.get('number')=='37' else F(0)
  cursor=F(0);last_start=F(0);events=defaultdict(list);controls=defaultdict(list);dirs=[]
  for x in m:
   if x.tag=='backup':cursor-=F(x.findtext('duration'))/(div*4)
   elif x.tag=='forward':cursor+=F(x.findtext('duration'))/(div*4)
   elif x.tag=='attributes':
    for c in x.findall('clef'):
     staff=c.get('number','1');clef='treble' if c.findtext('sign')=='G' else 'bass'
     controls[staff].append((max(F(0),cursor-shift),'\\clef '+quote(clef)));clefs[staff]=clef
   elif x.tag=='direction':
    time=max(F(0),cursor+F(x.findtext('offset','0'))/(div*4)-shift)
    if time<=length:dirs.append((time,x.findtext('staff','1'),x))
   elif x.tag=='note':
    grace=x.find('grace') is not None;chord=x.find('chord') is not None
    d=F(x.findtext('duration','0'))/(div*4)
    if not chord:last_start=cursor
    start=max(F(0),last_start-shift)
    v=x.findtext('voice','1')
    if shift and x.get('print-object')=='no' and last_start<shift:
     if not grace and not chord:cursor+=d
     continue
    ev={'time':start,'duration':d,'notes':[x],'grace':grace,'staff':x.findtext('staff','1')}
    if chord and events[v] and events[v][-1]['time']==start and events[v][-1]['grace']==grace:events[v][-1]['notes'].append(x)
    else:events[v].append(ev)
    if not grace and not chord:cursor+=d
  # Correct MuseScore's integer-tick rounding in the seven-note flourish.
  if primary and index==4 and m.get('number')=='120':
   for evs in events.values():
    group=[ev for ev in evs if ev['notes'][0].findtext('time-modification/actual-notes')=='7']
    if len(group)==7:
     start=group[0]['time']
     for j,ev in enumerate(group):ev['time']=start+F(j,112);ev['duration']=F(1,112)
  # MuseScore sometimes splits the lower member of a grace chord into
  # another voice. Merge it back into the ornament's leading chord.
  groups=defaultdict(lambda:defaultdict(list))
  for v,evs in events.items():
   for ev in evs:
    if ev['grace'] and any(n.get('print-object')!='no' and n.find('pitch') is not None for n in ev['notes']):groups[(ev['time'],ev['staff'])][v].append(ev)
  for group in groups.values():
   if len(group)<2:continue
   lead=max(group,key=lambda v:len(group[v]))
   if len(group[lead])<2:continue
   for v,evs in group.items():
    if v==lead or len(evs)!=1:continue
    for n in evs[0]['notes']:
     if n.get('print-object')!='no' and n.find('pitch') is not None:group[lead][0]['notes'].append(n)
    events[v].remove(evs[0])
  bars.append({'number':m.get('number'),'length':length,'events':events,'controls':controls,'directions':dirs,'xml':m,'key':key,'time':(beats,unit)})
 return bars

def slur_pairs(bars):
 accepted=set();pending={};dropped=0
 for bi,b in enumerate(bars):
  # XML order is voice-major, and each voice's order is chronological.
  for v,events in b['events'].items():
   for ei,ev in enumerate(events):
    for ni,n in enumerate(ev['notes']):
     for si,s in enumerate(n.findall('notations/slur')):
      if n.get('print-object')=='no':continue
      k=(v,s.get('number','1'));pos=(bi,v,ei,ni,si)
      if s.get('type')=='start':
       if k in pending:dropped+=1
       pending[k]=pos
      elif s.get('type')=='stop':
       if k in pending:accepted.add(pending.pop(k));accepted.add(pos)
       else:dropped+=1
 return accepted,dropped+len(pending)

def note_event(ev,bi,v,ei,slurs,forced_duration=None):
 ns=ev['notes'];visible=[n for n in ns if n.get('print-object')!='no'];d=ev['duration']
 if not visible:return skip(d) if not ev['grace'] else ''
 n=visible[0];stem=n.findtext('stem');prefix=('\\stemUp ' if stem=='up' else '\\stemDown ' if stem=='down' else '')
 pitches=[pitch(n)+('~' if len(visible)>1 and n.find('tie[@type="start"]') is not None else '') for n in visible if n.find('pitch') is not None]
 if pitches:
  body=(pitches[0] if len(pitches)==1 else '<'+' '.join(pitches)+'>')+(forced_duration or duration(n,d))
  if len(visible)==1 and n.find('tie[@type="start"]') is not None:body+='~'
 else:body=('R' if n.find('rest') is not None and n.find('rest').get('measure')=='yes' else 'r')+(forced_duration or duration(n,d))
 suffix=[]
 for ni,n in enumerate(ns):
  if n.get('print-object')=='no':continue
  for si,s in enumerate(n.findall('notations/slur')):
   if (bi,v,ei,ni,si) in slurs:
    num=s.get('number','1');suffix.append(('^' if s.get('placement')=='above' else '_' if s.get('placement')=='below' else '')+'\\='+num+'(' if s.get('type')=='start' else '\\='+num+')')
  if ni:continue
  for a in n.findall('notations/articulations/*'):
   mark={'staccato':'-.','tenuto':'--','accent':'->','strong-accent':'-^','staccatissimo':'-!','detached-legato':'-_','breath-mark':'\\breathe'}.get(a.tag)
   if mark:suffix.append(mark)
  for a in n.findall('notations/ornaments/*'):
   mark={'trill-mark':'\\trill','mordent':'\\mordent','inverted-mordent':'\\prall','turn':'\\turn','inverted-turn':'\\reverseturn'}.get(a.tag)
   if mark:suffix.append(mark)
   elif a.tag=='tremolo':
    if a.get('type')=='single':body+=':'+str(2**(int(a.text)+2))
  if n.find('notations/arpeggiate') is not None:suffix.append('\\arpeggio')
  for f in n.findall('notations/fermata'):suffix.append('\\fermata')
  for f in n.findall('notations/technical/fingering'):
   if (f.text or '').isdigit():suffix.append('-'+f.text)
 n=visible[0]
 beam=n.find('beam[@number="1"]')
 if beam is not None and pitches:
  if beam.text=='begin':suffix.append('[')
  elif beam.text=='end':suffix.append(']')
 return prefix+body+(' '+' '.join(suffix) if suffix else '')

def make_voice(bars,v,slurs,initial_staff,layout,break_voice):
 lines=['{', '  \\set tieWaitForNote = ##t'];staff=initial_staff
 for bi,b in enumerate(bars):
  tokens=[];pos=F(0);graces=[]
  if break_voice and bi:
   if b['number'] in layout['pages']:tokens.append('\\pageBreak')
   elif b['number'] in layout['systems']:tokens.append('\\break')
  consumed=set()
  evs=b['events'].get(v,[])
  for ei,ev in enumerate(evs):
   if ei in consumed:continue
   if ev['time']>pos:tokens.append(skip(ev['time']-pos));pos=ev['time']
   if ev['staff']!=staff:
    tokens.append('\\change Staff = '+quote(STAFF[ev['staff']]));staff=ev['staff']
   text=note_event(ev,bi,v,ei,slurs)
   if ev['grace']:
    if text:graces.append(text)
    continue
   if graces:
    leading_break=tokens.pop(0)+' ' if ev['time']==0 and tokens and tokens[0] in ['\\break','\\pageBreak'] else ''
    tokens.append('\\grace { '+leading_break+' '.join(graces)+' }');graces=[]
   if ev['time']<pos:raise ValueError((v,bi+1,'overlap',ev['time'],pos))
   trem=ev['notes'][0].find('notations/ornaments/tremolo[@type="start"]')
   if trem is not None and ei+1<len(evs):
    other=evs[ei+1]
    if other['notes'][0].find('notations/ornaments/tremolo[@type="stop"]') is not None:
     subdivision=2**(int(trem.text)+2)
     count=(ev['duration']+other['duration'])*subdivision/2
     tokens.append('\\repeat tremolo '+str(int(count))+' { '+note_event(ev,bi,v,ei,slurs,str(subdivision))+' '+note_event(other,bi,v,ei+1,slurs,str(subdivision))+' }')
     pos=other['time']+other['duration'];consumed.add(ei+1);continue
   tokens.append(text);pos=ev['time']+ev['duration']
  if graces:tokens.append('\\grace { '+' '.join(graces)+' }')
  if pos<b['length']:tokens.append(skip(b['length']-pos))
  if pos>b['length']:raise ValueError((v,bi+1,'overfull',pos,b['length']))
  lines.append('  % measure '+b['number'])
  lines.append('  '+' '.join(t for t in tokens if t)+' |')
 lines.append('}');return '\n'.join(lines)

def directions(bars,staff,kind):
 out=defaultdict(list)
 for bi,b in enumerate(bars):
  for t,st,d in b['directions']:
   if st!=staff:continue
   for dt in d.findall('direction-type/*'):
    mark=''
    if kind=='dynamics':
     if dt.tag=='dynamics' and len(dt):mark='\\'+dt[0].tag
     elif dt.tag=='wedge':mark={'crescendo':'\\<','diminuendo':'\\>','stop':'\\!'}.get(dt.get('type'),'')
    elif kind=='text':
     if dt.tag=='words':
      s=(dt.text or '').strip()
      if not s or s in ['PIANO'] or 'mémoire' in s or '‿' in s or s.startswith('=') or (bi==0 and s in ['Vif','Assez Vil','Allegretto','Allegro moderato']):continue
      # Remove the performance edition's repeated tempo reminders.
      if s=='Assez Vil':s='Assez vif'
      style='\\italic ' if dt.get('font-style')=='italic' else '\\bold ' if dt.get('font-weight')=='bold' else ''
      mark='^\\markup { '+style+quote(s)+' }'
     elif dt.tag=='pedal':
      mark={'stop':'\\sustainOff','change':'\\sustainOff \\sustainOn'}.get(dt.get('type'),'\\sustainOn')
     elif dt.tag=='octave-shift':
      val=0 if dt.get('type')=='stop' else (1 if dt.get('type')=='down' else -1)*(2 if dt.get('size')=='15' else 1)
      mark='\\ottava #'+str(val)
    if mark and mark not in out[(bi,t)]:out[(bi,t)].append(mark)
 return out

def timing(bars,staff,index,layout):
 dyn=directions(bars,staff,'dynamics');txt=directions(bars,staff,'text');lines=['{'];prevlength=None
 for bi,b in enumerate(bars):
  marks=defaultdict(list)
  if bi==0:
   marks[F(0)].extend(['\\key '+KEYS[b['key']]+' \\major','\\time '+str(b['time'][0])+'/'+str(b['time'][1])])
   if staff=='1':
    tempo,unit,bpm=TEMPOS[index];marks[F(0)].append('\\tempo '+quote(tempo)+' '+unit+' = '+str(bpm))
  if b['length']!=prevlength:
   marks[F(0)].append('\\set Timing.measureLength = #'+str(b['length'].numerator)+'/'+str(b['length'].denominator));prevlength=b['length']
  if staff=='1':
   if b['number'].isdigit():marks[F(0)].append('\\set Score.currentBarNumber = #'+b['number'])
   else:marks[F(0)].append('\\set Score.currentBarNumber = #140')
  for t,mark in b['controls'].get(staff,[]):marks[t].append(mark)
  if bi and b['key']!=bars[bi-1]['key']:marks[F(0)].append('\\key '+KEYS[b['key']]+' \\major')
  for (i,t),x in txt.items():
   if i==bi:marks[t].extend(x)
  # Dynamics are attached to spacers in this voice, separate from note voices.
  for (i,t),x in dyn.items():
   if i==bi:marks[t].extend(x)
  if staff=='1':
   for bl in b['xml'].findall('barline'):
    t=F(0) if bl.get('location')=='left' else b['length']
    rep=bl.find('repeat');ending=bl.find('ending')
    if rep is not None:marks[t].append('\\bar '+quote('.|:' if rep.get('direction')=='forward' else ':|.'))
    elif bl.findtext('bar-style') in ['light-light','light-heavy']:marks[t].append('\\bar '+quote('||' if bl.findtext('bar-style')=='light-light' else '|.'))
    if ending is not None:
     marks[t].append("\\set Score.repeatCommands = #'("+(('(volta #f) ' if ending.get('number')!='1' else '')+'(volta '+quote(ending.get('number')+'.')+')' if ending.get('type')=='start' else '(volta #f)')+")")
  pos=F(0);tokens=[]
  for t in sorted(marks):
   if t>pos:tokens.append(skip(t-pos));pos=t
   before=[];after=[]
   for mark in marks[t]:
    if mark.startswith('^') or mark.startswith('\\sustain') or mark in ['\\ppp','\\pp','\\p','\\mp','\\mf','\\f','\\ff','\\fff','\\fp','\\sf','\\sfz','\\sustainOn','\\sustainOff','\\<','\\>','\\!']:after.append(mark)
    else:before.append(mark)
   tokens.extend(before)
   if after:tokens.append('s1*0 '+' '.join(after))
  if pos<b['length']:tokens.append(skip(b['length']-pos))
  lines.append('  % measure '+b['number']+'\n  '+' '.join(tokens)+' |')
 lines.append('  \\bar "|."\n}');return '\n'.join(lines)


def ident(v):return ['Zero','One','Two','Three','Four','Five','Six','Seven'][int(v)]

def main():
 source=E.parse(ROOT/'piano/source/le-tombeau-de-couperin.musicxml').getroot()
 reference=E.parse(ROOT/'piano/source/layout-reference.musicxml').getroot()
 reports=[]
 for index,(ms,ref,name) in enumerate(zip(movements(source),movements(reference),NAMES)):
  bars=parse(ms,index)
  refbars={b['number']:b for b in parse(ref,index,primary=False)}
  for b in bars:
   if b['number'] in refbars:
    original_octaves=[(t,st,d) for t,st,d in b['directions'] if d.find('direction-type/octave-shift') is not None]
    b['directions']=[(t,st,d) for t,st,d in refbars[b['number']]['directions'] if t<=b['length'] and d.find('direction-type/octave-shift') is None]+original_octaves
   if index==0 and b['number']=='96':
    b['directions']=[(t,st,d) for t,st,d in b['directions'] if d.find('direction-type/pedal') is None]
    pedal=E.fromstring('<direction><direction-type><pedal type="change"/></direction-type></direction>')
    b['directions'].append((F(0),'2',pedal))
    b['directions']=[(t,st,d) for t,st,d in b['directions'] if d.find('direction-type/octave-shift') is None]
    for evs in b['events'].values():
     for ev in evs:
      for n in ev['notes']:
       octave=n.find('pitch/octave')
       if octave is not None:octave.text=str(int(octave.text)-1)
  slurs,dropped=slur_pairs(bars)
  pending_ties={};absolute=F(0);ties_removed=0
  def remove_start(n):
   nonlocal ties_removed
   for t in n.findall('tie[@type="start"]'):n.remove(t);ties_removed+=1
  for b in bars:
   for v,evs in b['events'].items():
    for ev in evs:
     at=absolute+ev['time']
     for n in ev['notes']:
      if n.find('pitch') is None or n.get('print-object')=='no':continue
      key=(v,tuple(n.findtext('pitch/'+k,'0') for k in ['step','alter','octave']))
      if key in pending_ties:
       old,expected=pending_ties.pop(key)
       if n.find('tie[@type="stop"]') is None or at!=expected:remove_start(old)
      if n.find('tie[@type="start"]') is not None:pending_ties[key]=(n,at+(F(0) if ev['grace'] else ev['duration']))
   absolute+=b['length']
  for n,expected in pending_ties.values():remove_start(n)
  systems=[m.get('number') for m in ref if m.find('print') is not None]
  layout={'systems':systems,'pages':[str(i) for i in PAGE_STARTS[index]]}
  voices=sorted(set(v for b in bars for v in b['events']),key=int)
  initial={v:next(ev['staff'] for b in bars for ev in b['events'].get(v,[])) for v in voices}
  # Drop voices containing only invisible playback material.
  voices=[v for v in voices if any(n.get('print-object')!='no' for b in bars for ev in b['events'].get(v,[]) for n in ev['notes'])]
  text=['% Working transcription. See README.md and EDITORIAL.md before use.']
  for v in voices:text.append('partVoice'+ident(v)+' = '+make_voice(bars,v,slurs,initial[v],layout,v==voices[0]))
  for st in ['1','2']:text.append('timing'+ident(st)+' = '+timing(bars,st,index,layout))
  prefix=name.split('-')[1]
  content='\n\n'.join(text)+'\n'
  content=content.replace('partVoice',prefix+'Voice').replace('timingOne',prefix+'TimingOne').replace('timingTwo',prefix+'TimingTwo')
  (DEST/'movements'/f'{name}.ily').write_text(content)
  score=['\\score {','  \\new PianoStaff \\with { connectArpeggios = ##t } <<']
  for st in ['1','2']:
   score.append('    \\new Staff = '+quote(STAFF[st])+' <<')
   score.append('      \\new Voice { \\timing'+ident(st)+' }')
   vs=[v for v in voices if initial[v]==st]
   for vi,v in enumerate(vs):score.append('      \\new Voice = "v'+v+'" { '+['\\voiceOne','\\voiceTwo','\\voiceThree','\\voiceFour'][min(vi,3)]+' \\partVoice'+ident(v)+' }')
   score.append('    >>')
  score+=['  >>','  \\layout { }','  \\midi { }','}']
  header='\\header {\n  title = "LE TOMBEAU DE COUPERIN"\n  subtitle = '+quote(TITLES[index])+'\n  composer = "MAURICE RAVEL"\n  dedication = \\markup \\italic '+quote('à la mémoire '+DEDICATIONS[index])+'\n  tagline = ##f\n}\n'
  wrapper='\\version "2.26.0"\n\\include "common.ily"\n\\include "movements/'+name+'.ily"\n'+header+'\n'+'\n'.join(score)+'\n'
  wrapper=wrapper.replace('partVoice',prefix+'Voice').replace('timingOne',prefix+'TimingOne').replace('timingTwo',prefix+'TimingTwo')
  (DEST/(name+'.ly')).write_text(wrapper)
  reports.append({'movement':name,'measures':len(bars),'slur_endpoints_unresolved':dropped,'playback_ties_removed':ties_removed,'voices':voices,'visible_pitches':sum(n.find('pitch') is not None and n.get('print-object')!='no' for b in bars for evs in b['events'].values() for ev in evs for n in ev['notes'])})
 parts=[];includes=[]
 for name in NAMES:
  wrapper=(DEST/(name+'.ly')).read_text()
  includes.append('\\include "movements/'+name+'.ily"')
  parts.append('  \\bookpart {\n'+wrapper[wrapper.index('\\header'):]+ '\n  }')
 (DEST/'le-tombeau-de-couperin.ly').write_text('\\version "2.26.0"\n\\include "common.ily"\n'+'\n'.join(includes)+'\n\\book {\n'+'\n'.join(parts)+'\n}\n')
 (DEST/'import-report.json').write_text(json.dumps(reports,indent=2)+'\n')

if __name__=='__main__':main()
