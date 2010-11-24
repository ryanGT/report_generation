#import numpy
#from scipy import isscalar, shape, imag, real, array

#import relpath

#from  IPython.Debugger import Pdb

#import pytexutils
#reload(pytexutils)
from pytexutils import *

#import texfilemixin

def FindHeader(pathin, fn='header.tex'):
    """Find filename fn by first walking up pathin and then looking in
    sys.path.  If not found, return None."""
    mypathlist = walkuplist(pathin)
    fullpathlist = mypathlist+os.sys.path
    for path in fullpathlist:
        curfp=os.path.join(path,fn)
        if os.path.exists(curfp):
            return curfp
    return None



class TexFileMixin(object):
    def SaveLatex(self, filename=None, ed=True):
        """Dump self.latexlist to a file, appending '\end{document}'
        if necessary and ed is True.  If filename is none, use
        self.path, but change the extenstion from .py to .tex."""
        if ed:
            edstr = '\\end{document}'
            if edstr not in self.latexlist:
                self.latexlist.append(edstr)
        if filename is None:
            pne, ext = os.path.splitext(self.path)
            self.latexpath = pne+'.tex'
        else:
            self.latexpath = filename
        writefile(self.latexpath, self.latexlist)


    def _FindBody(self):
        """Get the body of a latex document by returning everything in
        betwenn \begin{document} and \end{document}."""
        startind = findinlist(self.latexlist, '\\begin{document}')
        startind +=1#if \begin{document} is found, we want to skip the line containing it.  If it isn't found, findinlist will return -1 and we really want 0.
        endind = findinlist(self.latexlist, '\\end{document}')
        if endind == -1:
            return self.latexlist[startind:]
        else:
            return self.latexlist[startind:endind]
        
        
    def SaveNH(self, filename=None):
        """Save the body of a latex file to a file.  Note that even if
        filename is given, an _nh is inserted at the end before the
        .tex.."""
        if filename is None:
            pne, ext = os.path.splitext(self.path)
            self.latexpath = pne+'.tex'
        else:
            self.latexpath = filename
        pne2, ext = os.path.splitext(self.latexpath)
        self.nhpath = pne2+'_nh.tex'
        self.body = self._FindBody()
        writefile(self.nhpath, self.body)
        

    def AddHeader(self, headerpath=None, verbosity=1):
        """Search for a file named header.tex somewhere in sys.path
        and insert its contents at the begining of the Latex file."""
        # pathname=os.path.dirname(sys.argv[0])
        # self.scriptpath=os.path.abspath(pathname)
        # self.myprint("scriptpath="+self.scriptpath)
        # self.myprint("pathname="+pathname)
        check = findinlistre(self.latexlist, '\\\\input{.*header}')
        if check != -1:
            print('not adding a header')
            return
        fn="header.tex"
        headless=1      
        fp=""
        if headerpath is not None:
            if os.path.exists(headerpath):
                headless = 0
                fp = headerpath
        if headless:
            mypathlist = walkuplist(self.path)
            fullpathlist = mypathlist+os.sys.path
            for path in fullpathlist:
                curfp=os.path.join(path,fn)
                if os.path.exists(curfp):
                    headless=0
                    fp=curfp
                    break
        if headless:
            self.myprint("Could not find header.tex in any directory in os.sys.path")
            return None
        else:
            msg = "Loading header from "+fp
            if verbosity > 0:
                print(msg)
            add_bd = '\\begin{document}' not in self.latexlist
            header=readfile(fp)
            if header[-1]=='\\begin{document}':
                header.pop()
            if add_bd and ('\\begin{document}' not in header):
                header.append('\\begin{document}')
            if header[0].find('\\documentclass')==-1:
                header.insert(0,'\\documentclass[12pt]{article}')
            self.latexlist[:0]=header
            return not fp


    def HeaderInsert(self, insertlist):
        bdstr = '\\begin{document}'
        if not bdstr in self.latexlist:
            self.AddHeader()
        ind = self.latexlist.index(bdstr)
        self.latexlist[ind:ind]=insertlist
            


    def RunLatex(self, dvi=False, openviewer=False, sourcespecials=True, forceepstopdf=1):
        """Call Latex with file self.latexpath.  If dvi is True, regular
        Latex is called, otherwise pdflatex is called.  If openviewer
        is True, subprocess is called to open the file using either
        kdvi or acroread (note that this may not work on all
        platforms)."""
        if not dvi:
            self.EpstoPdf(force=forceepstopdf)
        return RunLatex(self.latexpath, dvi=dvi, openviewer=openviewer, sourcespecials=sourcespecials, log=None)

        
    def myprint(self, msg):
        """This is an awkward method put here for backward
        compatability.  Apparnetly, one of my old classes had a
        myprint method to make it easy to switch where log messages
        go.  I am just passing them to print for now."""
        print(msg)
        
