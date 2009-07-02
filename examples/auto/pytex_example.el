(TeX-add-style-hook "pytex_example"
 (lambda ()
    (LaTeX-add-labels
     "fig:exciting")
    (TeX-add-symbols
     '("inlinegraphic" 2)
     '("e" 1)
     '("picNR" 2)
     '("picR" 2)
     '("myvector" 3)
     '("M" 1)
     "be"
     "ee")
    (TeX-run-style-hooks
     "hypcap"
     "all"
     "mathrsfs"
     "amsmath"
     "listings"
     "color"
     "dvips"
     "hyperref"
     "times"
     "graphicx"
     "pdftex"
     "ifpdf"
     "fancyhdr"
     "latex2e"
     "art12"
     "article"
     "12pt")))

