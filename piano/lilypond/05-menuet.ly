\version "2.26.0"
\include "common.ily"
\include "movements/05-menuet.ily"
\header {
  title = "LE TOMBEAU DE COUPERIN"
  subtitle = "V. MENUET"
  composer = "MAURICE RAVEL"
  dedication = \markup \italic "à la mémoire de Jean Dreyfus"
  tagline = ##f
}

\score {
  \new PianoStaff \with { connectArpeggios = ##t } <<
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
  \layout { }
  \midi { }
}
