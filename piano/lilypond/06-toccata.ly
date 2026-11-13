\version "2.26.0"
\include "common.ily"
\include "movements/06-toccata.ily"
\header {
  title = "LE TOMBEAU DE COUPERIN"
  subtitle = "VI. TOCCATA"
  composer = "MAURICE RAVEL"
  dedication = \markup \italic "à la mémoire du capitaine Joseph de Marliave"
  tagline = ##f
}

\score {
  \new PianoStaff \with { connectArpeggios = ##t } <<
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
  \layout { }
  \midi { }
}
