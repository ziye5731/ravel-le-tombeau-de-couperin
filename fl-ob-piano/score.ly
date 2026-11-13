\version "2.26.0"
\include "common.ily"
\include "piano/01-prelude.ily"
\include "winds/01-prelude.ily"
\include "piano/02-fugue.ily"
\include "winds/02-fugue.ily"
\include "piano/03-forlane.ily"
\include "winds/03-forlane.ily"
\include "piano/04-rigaudon.ily"
\include "winds/04-rigaudon.ily"
\include "piano/05-menuet.ily"
\include "winds/05-menuet.ily"
\include "piano/06-toccata.ily"
\include "winds/06-toccata.ily"
\book {
  \bookpart {
\header {
  title = "LE TOMBEAU DE COUPERIN"
  subtitle = "I. PRÉLUDE"
  composer = "MAURICE RAVEL"
  dedication = \markup \italic "à la mémoire du lieutenant Jacques Charlot"
  tagline = ##f
}

\score {
  \new StaffGroup <<
    \new Staff = "flute" \with { instrumentName = "Flûte" shortInstrumentName = "Fl." midiInstrument = "flute" } { \preludeFlute }
    \new Staff = "oboe" \with { instrumentName = "Hautbois" shortInstrumentName = "Htb." midiInstrument = "oboe" } { \preludeOboe }
    \new PianoStaff \with { instrumentName = "Piano" shortInstrumentName = "Pno." connectArpeggios = ##t } <<
    \new Staff = "upper" <<
      \new Voice { \preludeTimingOne }
      \new Voice = "v1" { \voiceOne \preludeVoiceOne }
      \new Voice = "v2" { \voiceTwo \preludeVoiceTwo }
      \new Voice = "v3" { \voiceThree \preludeVoiceThree }
      \new Voice = "v4" { \voiceFour \preludeVoiceFour }
    >>
    \new Staff = "lower" <<
      \new Voice { \preludeTimingTwo }
      \new Voice = "v5" { \voiceOne \preludeVoiceFive }
      \new Voice = "v6" { \voiceTwo \preludeVoiceSix }
    >>
    >>
  >>
  \layout { }
  \midi { }
}

  }
  \bookpart {
\header {
  title = "LE TOMBEAU DE COUPERIN"
  subtitle = "II. FUGUE"
  composer = "MAURICE RAVEL"
  dedication = \markup \italic "à la mémoire du sous-lieutenant Jean Cruppi"
  tagline = ##f
}

\score {
  \new StaffGroup <<
    \new Staff = "flute" \with { instrumentName = "Flûte" shortInstrumentName = "Fl." midiInstrument = "flute" } { \fugueFlute }
    \new Staff = "oboe" \with { instrumentName = "Hautbois" shortInstrumentName = "Htb." midiInstrument = "oboe" } { \fugueOboe }
    \new PianoStaff \with { instrumentName = "Piano" shortInstrumentName = "Pno." connectArpeggios = ##t } <<
    \new Staff = "upper" <<
      \new Voice { \fugueTimingOne }
      \new Voice = "v1" { \voiceOne \fugueVoiceOne }
      \new Voice = "v2" { \voiceTwo \fugueVoiceTwo }
    >>
    \new Staff = "lower" <<
      \new Voice { \fugueTimingTwo }
      \new Voice = "v5" { \voiceOne \fugueVoiceFive }
    >>
    >>
  >>
  \layout { }
  \midi { }
}

  }
  \bookpart {
\header {
  title = "LE TOMBEAU DE COUPERIN"
  subtitle = "III. FORLANE"
  composer = "MAURICE RAVEL"
  dedication = \markup \italic "à la mémoire du lieutenant Gabriel Deluc"
  tagline = ##f
}

\score {
  \new StaffGroup <<
    \new Staff = "flute" \with { instrumentName = "Flûte" shortInstrumentName = "Fl." midiInstrument = "flute" } { \forlaneFlute }
    \new Staff = "oboe" \with { instrumentName = "Hautbois" shortInstrumentName = "Htb." midiInstrument = "oboe" } { \forlaneOboe }
    \new PianoStaff \with { instrumentName = "Piano" shortInstrumentName = "Pno." connectArpeggios = ##t } <<
    \new Staff = "upper" <<
      \new Voice { \forlaneTimingOne }
      \new Voice = "v1" { \voiceOne \forlaneVoiceOne }
      \new Voice = "v2" { \voiceTwo \forlaneVoiceTwo }
      \new Voice = "v4" { \voiceThree \forlaneVoiceFour }
    >>
    \new Staff = "lower" <<
      \new Voice { \forlaneTimingTwo }
      \new Voice = "v5" { \voiceOne \forlaneVoiceFive }
      \new Voice = "v6" { \voiceTwo \forlaneVoiceSix }
    >>
    >>
  >>
  \layout { }
  \midi { }
}

  }
  \bookpart {
\header {
  title = "LE TOMBEAU DE COUPERIN"
  subtitle = "IV. RIGAUDON"
  composer = "MAURICE RAVEL"
  dedication = \markup \italic "à la mémoire de Pierre et Pascal Gaudin"
  tagline = ##f
}

\score {
  \new StaffGroup <<
    \new Staff = "flute" \with { instrumentName = "Flûte" shortInstrumentName = "Fl." midiInstrument = "flute" } { \rigaudonFlute }
    \new Staff = "oboe" \with { instrumentName = "Hautbois" shortInstrumentName = "Htb." midiInstrument = "oboe" } { \rigaudonOboe }
    \new PianoStaff \with { instrumentName = "Piano" shortInstrumentName = "Pno." connectArpeggios = ##t } <<
    \new Staff = "upper" <<
      \new Voice { \rigaudonTimingOne }
      \new Voice = "v1" { \voiceOne \rigaudonVoiceOne }
      \new Voice = "v2" { \voiceTwo \rigaudonVoiceTwo }
    >>
    \new Staff = "lower" <<
      \new Voice { \rigaudonTimingTwo }
      \new Voice = "v5" { \voiceOne \rigaudonVoiceFive }
      \new Voice = "v6" { \voiceTwo \rigaudonVoiceSix }
    >>
    >>
  >>
  \layout { }
  \midi { }
}

  }
  \bookpart {
\header {
  title = "LE TOMBEAU DE COUPERIN"
  subtitle = "V. MENUET"
  composer = "MAURICE RAVEL"
  dedication = \markup \italic "à la mémoire de Jean Dreyfus"
  tagline = ##f
}

\score {
  \new StaffGroup <<
    \new Staff = "flute" \with { instrumentName = "Flûte" shortInstrumentName = "Fl." midiInstrument = "flute" } { \menuetFlute }
    \new Staff = "oboe" \with { instrumentName = "Hautbois" shortInstrumentName = "Htb." midiInstrument = "oboe" } { \menuetOboe }
    \new PianoStaff \with { instrumentName = "Piano" shortInstrumentName = "Pno." connectArpeggios = ##t } <<
    \new Staff = "upper" <<
      \new Voice { \menuetTimingOne }
      \new Voice = "v1" { \voiceOne \menuetVoiceOne }
      \new Voice = "v2" { \voiceTwo \menuetVoiceTwo }
      \new Voice = "v3" { \voiceThree \menuetVoiceThree }
      \new Voice = "v4" { \voiceFour \menuetVoiceFour }
    >>
    \new Staff = "lower" <<
      \new Voice { \menuetTimingTwo }
      \new Voice = "v5" { \voiceOne \menuetVoiceFive }
      \new Voice = "v6" { \voiceTwo \menuetVoiceSix }
    >>
    >>
  >>
  \layout { }
  \midi { }
}

  }
  \bookpart {
\header {
  title = "LE TOMBEAU DE COUPERIN"
  subtitle = "VI. TOCCATA"
  composer = "MAURICE RAVEL"
  dedication = \markup \italic "à la mémoire du capitaine Joseph de Marliave"
  tagline = ##f
}

\score {
  \new StaffGroup <<
    \new Staff = "flute" \with { instrumentName = "Flûte" shortInstrumentName = "Fl." midiInstrument = "flute" } { \toccataFlute }
    \new Staff = "oboe" \with { instrumentName = "Hautbois" shortInstrumentName = "Htb." midiInstrument = "oboe" } { \toccataOboe }
    \new PianoStaff \with { instrumentName = "Piano" shortInstrumentName = "Pno." connectArpeggios = ##t } <<
    \new Staff = "upper" <<
      \new Voice { \toccataTimingOne }
      \new Voice = "v2" { \voiceOne \toccataVoiceTwo }
    >>
    \new Staff = "lower" <<
      \new Voice { \toccataTimingTwo }
      \new Voice = "v1" { \voiceOne \toccataVoiceOne }
      \new Voice = "v5" { \voiceTwo \toccataVoiceFive }
      \new Voice = "v6" { \voiceThree \toccataVoiceSix }
    >>
    >>
  >>
  \layout { }
  \midi { }
}

  }
}
