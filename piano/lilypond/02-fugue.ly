\version "2.26.0"
\include "common.ily"
\include "movements/02-fugue.ily"
\header {
  title = "LE TOMBEAU DE COUPERIN"
  subtitle = "II. FUGUE"
  composer = "MAURICE RAVEL"
  dedication = \markup \italic "à la mémoire du sous-lieutenant Jean Cruppi"
  tagline = ##f
}

\score {
  \new PianoStaff \with { connectArpeggios = ##t } <<
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
  \layout { }
  \midi { }
}
