

.. role:: ref

.. role:: label


.. role:: latex(raw)
     :format: latex


.. default-role:: latex


.. role:: inline


.. sectnum::
  :depth: 3


.. raw::  latex

    \newcommand*{\docutilsroleref}{\ref}
    \newcommand*{\docutilsrolelabel}{\label}
    \newcommand*{\docutilsroleinline}[1]{\lstinline!#1!}
    \newcommand{\mytitle}[1]{\textbf{\flushleft \Large #1}}
    \newcommand{\mytitlel}[1]{\textbf{\flushleft \large #1}}
    \newcommand{\sat}{\textrm{sat}}
    \newcommand{\sign}{\textrm{sign}}
    \newcommand{\sgn}{\textrm{sgn}}
    \newcommand{\inlinegraphic}[2]{\begin{center}\includegraphics[width=#1]{#2}\end{center}}
    \def\*#1{\mathbf{#1}}
    \newcommand{\M}[1]{\mathbf{#1}}
    \newcommand{\roboticstitle}[1]{
       \begin{tabular*}
           {\textwidth}
           {@{\extracolsep{\fill}}lcr} ME 454/ECE 467 - Summer 2015 
               & #1 & Name:\rule{1.75in}{1pt}
       \end{tabular*}
    }



