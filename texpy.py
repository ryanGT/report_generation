"""This module is the counter part to pytex.  The idea in this module
is to place Python code within a Latex document so that it gets
executed and the result gets substituted back into Latex.

The basic idea is that Python code will be inserted into the Latex
using syntax like:
\py{  }, \pyno{  }, \pyans{  }, and \pyfig{  }.

Each chunk will be converted to the appropriate OuterBlock from pytex,
executed in one namespace, and the result of ToLatex(echo=0) will be
substituted back into the Latex file."""

import pytex
reload(pytex)

import re, copy, os, pdb

from rwkmisc import rwkstr

from IPython.core.debugger import Pdb

import texfilemixin

from pytexutils import *

def CountCurlies(strin):
    mystr = rwkstr(strin)
    numleft = len(mystr.findall('{'))
    numright = len(mystr.findall('}'))
    return numleft, numright


def BalanceCurlies(strin):
    outstr = ''
    rest = strin
    ind = len(rest)
    cont = True
    while ind != -1 and cont:
        ind = rest.find('}')
        if ind > -1:
            outstr += rest[0:ind]
            rest = rest[ind+1:]
            no, nc = CountCurlies(outstr)
            if no == nc:
                cont = False
                return outstr
            else:
                outstr += '}'
        else:
            outstr += rest
    return outstr


default_envmap = {'py':pytex.OuterBlock, \
                  'pyno':pytex.NoOutBlock, \
                  'pyans':pytex.AnswerBlock, \
                  'pyfig':pytex.FigureBlock, \
                  'pyq':pytex.QuestionBlock, \
                  'pyfigans':pytex.AnsFigureBlock, \
                  'pyi':pytex.PyInLineBlock, \
                  'pyloop':pytex.LoopBlock, \
                  'pyarb':pytex.ArbitraryBlock, \
                  'pyine':pytex.PyInLineNoExecuteBlock, \
                  'pyne':pytex.PyNoExecuteBlock,
                  'pyanscom':pytex.PyAnsCommentBlock,
                  'pyecho':pytex.EchoBlock,
                  'pystd':pytex.StdoutBlock,
                  'pyinput':pytex.InputFile,
                  }


exclude_lhs_list = [pytex.LoopBlock, pytex.ArbitraryBlock]

class TexPyFile(texfilemixin.TexFileMixin):#PythonFile):
    """This class represents a Latex file with some Python code
    embedded in it."""
    def __init__(self, filepath, envmap=None):
        """Create a Latex file with embedded Python code."""
        if envmap is None:
            #print('using default_envmap:'+str(default_envmap.keys()))
            envmap = default_envmap
        self.envmap = envmap
        self.envstr = '|'.join(self.envmap.keys())
        self.pat = r'^\\('+self.envstr+'){'
        self.p = re.compile(self.pat)
        self.envmap = envmap
        self.path = filepath
        basepath, filename = os.path.split(self.path)
        self.basepath = basepath
        rawlist = pytex.readfile(self.path)
        self.rawlist = rawlist
        self.lines = copy.copy(self.rawlist)
        self.ind = 0
        self.lhslist = []


    def HasPython(self):
        """Check to see if the file actually contains any Python code."""
        oldind = copy.copy(self.ind)
        self.ind = 0
        mybool = self.FindNextEnv()
        self.ind = oldind#reset ind
        return bool(mybool)



    def FindNextEnv(self, listname='lines'):
        """Find the next line matching self.p (the re.compile-ed
        version of self.pat), starting at line self.ind.

        The listname variable allows using this method on various
        lists within self, i.e. for texmaxima I need one list that
        doesn't get modified and one that does, so I have a
        self.rawlist and self.lines (or something like that)."""
        myvect = getattr(self, listname)
        for n, line in enumerate(myvect[self.ind:]):
            q = self.p.search(line)
            if q:
                self.matchline = self.ind+n
                self.ind = self.matchline+1#setup for next search, you
                                           #may not want this +1 if
                                           #the match gets removed and
                                           #replaced with nothing.
                return self.matchline
        return None#no match is left if we got this far


    def FindEndofEnv(self, matchline=None, listname='lines'):
        myvect = getattr(self, listname)
        if matchline is None:
            matchline = self.matchline
        n = -1
        match = False
        numleft = 0
        numright = 0
        while (not match) and (n < len(self.lines)):
            n += 1
            curline = rwkstr(myvect[matchline+n])
            numleft += len(curline.findall('{'))
            numright += len(curline.findall('}'))
            if numright >= numleft:
                match = True
        if match:
            self.endline = matchline+n
            return self.endline
        else:
            return None


    def PopEnv(self, startline=None, endline=None, clear=True, listname='lines'):
        myvect = getattr(self, listname)
        if startline is None:
            startline = self.matchline
        if endline is None:
            endline = self.endline+1
        outlist = myvect[startline:endline]
        if startline==endline:#make sure the {'s  and }'s are balanced
            outstr = BalanceCurlies(outlist[0])
            outlist = [outstr]
        if clear:
            myvect[startline:endline] = []
        return outlist


    def PopNext(self, clear=True, listname='lines'):
        if self.FindNextEnv(listname=listname):#sets self.matchline
            self.FindEndofEnv(listname=listname)#sets self.endline
            outlist = self.PopEnv(clear=clear, listname=listname)
            if clear:
                self.ind = self.matchline#reset the place where we start the search
            else:
                self.ind = self.endline+1
            return outlist
        else:
            return None


    def _CleanChunk(self, chunk):
        """Extract the Python code from \pyenv{  }"""
        mystr = '\n'.join(chunk)
        p2 = re.compile(self.pat+'(.*)}', re.DOTALL)
        q2 = p2.search(mystr)
        code = q2.group(2)
        code = BalanceCurlies(code)
        nl, nr = CountCurlies(code)
        assert nl==nr, "Number of left and right curly braces not equal:"+code
        envkey = q2.group(1)
        codelist = code.split('\n')
        return envkey, codelist


    def Execute(self, namespace={}, answer=False, replacelist=None, echo=0, **kwargs):
        """Execute each Python block, substituting the Latex output.
        Because we will be removing lines of varying length from the
        Latex list, it seems necessary to execute the code chunks and
        grab their output one-by-one, substituting the output back in
        as we go along."""
        keepgoing = True
        self.lhslist = []
        n = 0
        while keepgoing and (n < len(self.lines)):
            chunk = self.PopNext()
            if chunk:
                envkey, codelist = self._CleanChunk(chunk)
                curclass = self.envmap[envkey]
                block = curclass(codelist)
                block.Execute(namespace=namespace, answer=answer, **kwargs)
                curlatex = block.ToLatex(echo=echo, answer=answer, replacelist=replacelist, **kwargs)
                if type(curlatex) == str:
                    curlatex = [curlatex]
                curN = len(curlatex)
                self.lhslist.extend(block.FindLHSs())
                self.lines[self.matchline:self.matchline] = curlatex
                self.ind = self.matchline+curN
            else:
                keepgoing = False
            n += 1
        self.latexlist = self.lines
        return self.lines


    def FindLHSs(self):
        """Since you can't really go back and find it if the code has
        been executed, you are stuck with trusting that is it right.
        If the code has never been executed, this will be empty."""
        return self.lhslist


    def EpstoPdf(self, force=True):
        return None


    def ExportPython(self):
        """Dump the file to a python file, omitting the body of the text
        (i.e. all python commands only)."""
        oldind = copy.copy(self.ind)
        self.ind = 0
        pylines = []
        keepgoing = True
        n = 0
        while keepgoing and (n < len(self.lines)):
            chunk = self.PopNext()
            if chunk:
                envkey, codelist = self._CleanChunk(chunk)
                for n, line in enumerate(codelist):
                    if line.find('label=') == 0:
                        line = '#'+line
                        codelist[n] = line
                pylines.extend(codelist)
            else:
                keepgoing = False
            n += 1
        pne, ext = os.path.splitext(self.path)
        pathout = pne+'_out.py'
        pytex.writefile(pathout, pylines)
        self.ind = oldind


#TexPyFile derives from pytex.PythonFile for the sake of inheriting
#some useful methods like SaveLatex and AddHeader.  The ones below
#don't really make any sense for TexPyFile, so this is my way of
#uninheriting them:
##     def ToLatex(self):
##         raise NotImplementedError, "Method inherited from parent makes no sense"


##     def ToBlocks(self):
##         raise NotImplementedError, "Method inherited from parent makes no sense"


##     def ToListing(self):
##         raise NotImplementedError, "Method inherited from parent makes no sense"



class TexPYPFile(TexPyFile):#PythonFile):
    """This class represents a Latex file with some Python code
    embedded in it."""
    def __init__(self, filepath, envmap=None):
        """Create a Latex file with embedded Python code."""
        if envmap is None:
            envmap = default_envmap
#            envmap = {'py':pytex.OuterBlock, 'pyno':pytex.NoOutBlock, 'pyans':pytex.AnswerBlock, 'pyfig':pytex.FigureBlock, 'pyi':pytex.PyInLineBlock, 'pyq':pytex.QuestionBlock, 'pyine':pytex.PyInLineNoExecuteBlock}
        self.envmap = envmap
        self.envstr = '|'.join(self.envmap.keys())
        self.pat = r'('+self.envstr+'){'
        self.p = re.compile(self.pat)
        self.envmap = envmap
        self.path = filepath
        basepath, filename = os.path.split(self.path)
        self.basepath = basepath
        rawlist = pytex.readfile(self.path)
        self.rawlist = rawlist
        self.lines = copy.copy(self.rawlist)
        self.ind = 0
        self.lhslist = []


    def Execute(self, namespace={}, answer=False, **kwargs):
        """Execute each Python block, substituting the Latex output.
        Because we will be removing lines of varying length from the
        Latex list, it seems necessary to execute the code chunks and
        grab their output one-by-one, substituting the output back in
        as we go along."""
        keepgoing = True
        self.lhslist = []
        n = 0
        self.counter = None
        self.p2 = re.compile(self.pat+r'(.*?)}')
        while keepgoing and (n < len(self.lines)):
            chunk = self.PopNext()
            if chunk:
                envkey, codelist = self._CleanChunk(chunk)
                curclass = self.envmap[envkey]
                block = curclass(codelist)
                block.Execute(namespace=namespace, **kwargs)
                curlatex = block.ToLatex(echo=0, answer=answer, count=self.counter, **kwargs)
                if hasattr(block,'counter'):
                    self.counter = block.counter
                curN = len(curlatex)
                self.lhslist.extend(block.FindLHSs())
                if isinstance(block, pytex.PyInLineBlock):
                    q2 = self.p2.search(chunk[0])
                    assert q2.group(2).find(codelist[0])>-1, "problem with matching inline Python code:\n q2.group(2)="+q2.group(2)+"\n codelist[0]="+codelist[0]
                    rlatex = curlatex.replace('\\','\\\\')
                    repchunk = self.p2.sub(rlatex, chunk[0], count=1)
                    self.lines[self.matchline:self.matchline] = [repchunk]
                else:
                    self.lines[self.matchline:self.matchline] = curlatex
                    self.ind = self.matchline+curN
            else:
                keepgoing = False
            n += 1
        self.latexlist = self.lines
        return self.lines


    def SavePYP(self, filename=None):
        """Dump self.latexlist to a file.  If filename is none, use
        self.path, but add _out.pyp."""
        if filename is None:
            pne, ext = os.path.splitext(self.path)
            self.pyppath = pne+'_out.pyp'
        else:
            self.pyppath = filename
        writefile(self.pyppath, self.latexlist)
        return self.pyppath
