\version "2.26.0"
\include "common.ily"
\include "movements/03-forlane.ily"
\header {
  title = "LE TOMBEAU DE COUPERIN"
  subtitle = "III. FORLANE"
  composer = "MAURICE RAVEL"
  dedication = \markup \italic "à la mémoire du lieutenant Gabriel Deluc"
  tagline = ##f
}

\score {
  \new PianoStaff \with { connectArpeggios = ##t } <<
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
  \layout { }
  \midi { }
}
