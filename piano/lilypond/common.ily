\version "2.26.0"
#(set-global-staff-size 16)
\midi {
  \context { \Staff midiInstrument = "acoustic grand" }
}
\paper {
  #(set-paper-size "a4")
  top-margin = 9\mm
  bottom-margin = 13\mm
  left-margin = 10\mm
  right-margin = 10\mm
  indent = 12\mm
  short-indent = 0\mm
  ragged-last-bottom = ##f
  print-page-number = ##t
  first-page-number = #2
  bookTitleMarkup = \markup \column {
    \fill-line { \fontsize #4 \bold \fromproperty #'header:title }
    \vspace #1.5
    \fill-line { \fontsize #3 \bold \fromproperty #'header:subtitle }
    \vspace #1.2
    \fill-line {
      \fontsize #-1 \fromproperty #'header:dedication
      \fontsize #1 \fromproperty #'header:composer
    }
    \vspace #0.8
  }
  scoreTitleMarkup = ##f
  oddHeaderMarkup = \markup \fill-line { "" \fromproperty #'page:page-number-string "" }
  evenHeaderMarkup = \oddHeaderMarkup
  oddFooterMarkup = ##f
  evenFooterMarkup = ##f
  system-system-spacing.basic-distance = #17
  system-system-spacing.minimum-distance = #12
  system-system-spacing.padding = #3
}
\layout {
  \context {
    \Score
    autoBeaming = ##f
    \override BarNumber.break-visibility = ##(#f #f #f)
    \override MetronomeMark.font-size = #0
    \override TextScript.font-size = #-1
  }
  \context {
    \PianoStaff
    \override StaffGrouper.staff-staff-spacing.basic-distance = #11
    \override StaffGrouper.staff-staff-spacing.minimum-distance = #8
    \override StaffGrouper.staff-staff-spacing.padding = #2
  }
  \context { \Staff \accidentalStyle piano }
}
