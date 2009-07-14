from pylab import *
from scipy import *

#pyno
a = 7
#! a pyno block doesn't show up in the latex output

#pybody
t = arange(0,1,0.01)
y = sin(2*pi*t)

#Normal comments become latex text.

#! Comments with an ! second don't get passed to latex.

#pyfig
#filename:example_plot.eps
#caption:An exciting figure.
#label:fig:exciting
figure(1)
clf()
plot(t, y)

#Note: a \texttt{pyfig} block must be immediately followed by a
#\#filename:\path{file_name} line

#Figure~\ref{fig:exciting} is pretty cool.
