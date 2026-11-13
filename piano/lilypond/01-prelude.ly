\version "2.26.0"
\include "common.ily"
\include "movements/01-prelude.ily"
\header {
  title = "LE TOMBEAU DE COUPERIN"
  subtitle = "I. PRÉLUDE"
  composer = "MAURICE RAVEL"
  dedication = \markup \italic "à la mémoire du lieutenant Jacques Charlot"
  tagline = ##f
}

\score {
  \new PianoStaff \with { connectArpeggios = ##t } <<
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
  \layout { }
  \midi { }
}
