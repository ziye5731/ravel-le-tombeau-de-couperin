\version "2.26.0"
#(set-global-staff-size 13)
\paper {
  #(set-paper-size "a4")
  top-margin = 12\mm
  bottom-margin = 12\mm
  left-margin = 14\mm
  right-margin = 12\mm
  indent = 22\mm
  short-indent = 12\mm
  ragged-last-bottom = ##f
  print-page-number = ##t
  bookTitleMarkup = \markup \column {
    \fill-line { \fontsize #3 \bold \fromproperty #'header:title }
    \vspace #0.8
    \fill-line { \fontsize #2 \bold \fromproperty #'header:subtitle }
    \vspace #0.8
    \fill-line { \fontsize #-1 \fromproperty #'header:dedication \fromproperty #'header:composer }
    \vspace #0.5
  }
  scoreTitleMarkup = ##f
  system-system-spacing.basic-distance = #16
  system-system-spacing.minimum-distance = #12
  system-system-spacing.padding = #3
}
\layout {
  \context {
    \Score
    autoBeaming = ##f
    barNumberVisibility = #all-bar-numbers-visible
    \override BarNumber.break-visibility = ##(#f #t #t)
    \override BarNumber.font-size = #-2
    \override BarNumber.padding = #2
  }
  \context { \Staff \accidentalStyle piano }
}
\midi { \context { \Staff midiInstrument = "acoustic grand" } }
