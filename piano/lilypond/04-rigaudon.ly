\version "2.26.0"
\include "common.ily"
\include "movements/04-rigaudon.ily"
\header {
  title = "LE TOMBEAU DE COUPERIN"
  subtitle = "IV. RIGAUDON"
  composer = "MAURICE RAVEL"
  dedication = \markup \italic "à la mémoire de Pierre et Pascal Gaudin"
  tagline = ##f
}

\score {
  \new PianoStaff \with { connectArpeggios = ##t } <<
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
  \layout { }
  \midi { }
}
