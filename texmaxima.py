import pytex
#reload(pytex)

import texpy
#reload(texpy)

import re, copy, os, glob, pdb

from rwkmisc import rwkstr

from IPython.core.debugger import Pdb

#import textfiles
#reload(textfiles)

#import textfiles.latexlist
#from textfiles.latexlist import ParseMaximaOutput
import parse_maxima
from parse_maxima import ParseMaximaOutput

import texfilemixin
import wxmlit

import pytexutils
#reload(pytexutils)

from pytexutils import *

#################
##
## Example Maxima input script:
##
## eq1:x+y=5$
## tex(eq1, "temp_eqs/maxeq0.tex")$
## eq2:x-y=7$
## tex(eq2, "temp_eqs/maxeq1.tex")$
## solve([eq1,eq2],[x,y])$
## tex(solve([eq1,eq2],[x,y]), "temp_eqs/maxeq2.tex")$
##
#################

def keepme(item):
    badlist = ['\\mlabel','\\label','\\parseopts','\\opts']
    for pat in badlist:
        if pat in item:
            return False
    return True


def stripcodelist(codelist):
    """Remove all empty lines, all lines containing \mlabel, and all
    lines containing \parseopts from codelist."""
    outlist = [item for item in codelist if item]
    finallist = [item for item in outlist if keepme(item)]
    finallist = FilterComments(finallist)
    return finallist



def FilterComments(listin):
    compat = re.compile('^\\s*%')
    listout = [item for item in listin if not compat.match(item)]
    return listout


class MaximaLine:
    """Class representing one line of Maxima code extracted from a
    Latex document."""
    def __init__(self, line, ind, noout=False, folder='temp_eqs', basename='temp_eq_', label=None, suppressenv=False, suppresslhs=False, **kwargs):
        """Create an instance of MaximaLine.  line is the Maxima code,
        ind is the line number from the original file.  This will be
        used to name and locate the tex output file from Maxima."""
        print('line='+line)
        print('noout='+str(noout))
        self.line = line
        self.ind = ind
        self.noout = noout
        self.basename = basename
        self.folder = folder
        self.label = label
        self.suppressenv = suppressenv
        self.suppresslhs = suppresslhs
        keylist = ['prepend','append','lhs']
        for key in keylist:
            if kwargs.has_key(key):
                val = kwargs[key]
            else:
                val = ''
            setattr(self, key, val)
        self.kwargs = kwargs


    def BuildFilename(self, fmt='%0.3i'):
        self.filename = self.basename+fmt%self.ind+'.tex'
        self.path = os.path.join(self.folder, self.filename)


    def BuildSaveLine(self):
        if not hasattr(self, 'path'):
            self.BuildFilename()
        self.saveline = 'tex(%, "'+self.path+'")$'
        return self.saveline


    def BuildMaximaLines(self):
        if not hasattr(self, 'path'):
            self.BuildFilename()
        firstline = self.line
        if firstline[-1]!=';' and firstline[-1]!='$':
            firstline +=';'
        maximaout = [firstline]
        if not self.noout:
            self.BuildSaveLine()
            maximaout.append(self.saveline)
        self.maximalines = maximaout
        return self.maximalines


    def FindLHS(self):
        eqind = self.line.find('=')
        parenind = self.line.find('(')
        cind = self.line.find(':')
        if cind > -1:
            out = self.line[0:cind]
        else:
            out = self.line
        if eqind > -1:
            if parenind > -1:
                if eqind < parenind:#this is to avoid problems with lines like "Um2:subst(m=m2, Um)" where the equals sign doesn't mean this is an equation
                    out = ''#equals sign occurs before parenthesis and
                            #this is probably a legit equation
        self.lhs = out
        return self.lhs


    def BuildLatexLines(self, echo=0, env='equation', replacelist=None, **kwargs):
        self.texlines = []
        if echo==1:
            raise NotImplementedError, "Need a means to put verbatim Maxima code in Latx."
        if self.noout:
            self.rawlatex = []
            return self.texlines
        assert os.path.exists(self.path), "MaximaLine cannot find self.path:"+self.path
        inlines = pytex.readfile(self.path)
        if self.suppresslhs:
            self.lhs = ''
        else:
            if not self.lhs:
                self.FindLHS()
        outlines = ParseMaximaOutput(inlines, lhs=self.lhs)
        self.rawlatex = copy.copy(outlines)
        if replacelist is not None:
            outlines = replacelist.Replace(outlines)
        if self.prepend:
            outlines[0] = self.prepend + outlines[0]
        if self.append:
            outlines[-1] = outlines[-1] + self.append
        if not self.suppressenv:
            self.texlines.append('\\begin{'+env+'}')
        self.texlines.extend(outlines)
        if self.label:
            self.texlines.append('\\label{'+self.label+'}')
        if not self.suppressenv:
            self.texlines.append('\\end{'+env+'}')
        return self.texlines


    def FindReplacePats(self):
        self.findpats = FindReplacementCandidates(self.rawlatex)
        return self.findpats


class MaximaContLine(MaximaLine):
    def __init__(self, line, ind, noout=False, folder='temp_eqs', basename='temp_eq_', label=None, suppressenv=True, suppresslhs=True, **kwargs):
        MaximaLine.__init__(self, line, ind, noout=noout, folder=folder, basename=basename, label=label, suppressenv=suppressenv, suppresslhs=suppresslhs, **kwargs)

##     def BuildLatexLines(self, echo=0, env='equation', replacelist=None):
##         MaximaLine.BuildLatexLines(
##         self.texlines = []
##         if echo==1:
##             raise NotImplementedError, "Need a means to put verbatim Maxima code in Latx."
##         if self.noout:
##             self.rawlatex = []
##             return self.texlines
##         assert os.path.exists(self.path), "MaximaLine cannot find self.path:"+self.path
##         inlines = pytex.readfile(self.path)
##         self.FindLHS()
##         outlines = ParseMaximaOutput(inlines)
##         self.rawlatex = copy.copy(outlines)
##         if replacelist is not None:
##             outlines = replacelist.Replace(outlines)
##         self.texlines.extend(outlines)
##         if self.label:
##             self.texlines.append('\\label{'+self.label+'}')
##         return self.texlines


class MaximaBlock:
    def __init__(self, listin, startline, noout=False, folder='temp_eqs', basename='temp_eq_', **kwargs):
        self.list = listin
        self.startline = startline
        self.noout = noout
        self.folder = folder
        self.basename = basename
        self.kwargs = kwargs


    def BuildLines(self, lineclass=MaximaLine):
        self.lines = []
        curlabel = None
        labelpat = re.compile('^\\s*\\\\m*label{(.*?)}')
        optspat = re.compile('^\\s*\\\\opts{(.*)}')
        compat = re.compile('^\\s*%')
        optdict = {}
        for n, curstring in enumerate(self.list):
            q0 = compat.match(curstring)
            if not q0:
                q = labelpat.match(curstring)
                if q:
                    curlabel = q.group(1)
                else:
                    q2 = optspat.match(curstring)
                    if q2:
                        optstr = q2.group(1)
                        optdict = StrToDict(optstr)
                    else:
                        curline = lineclass(curstring, n+self.startline, noout=self.noout, folder=self.folder, basename=self.basename, label=curlabel, **optdict)
                        self.lines.append(curline)
                        curlabel = None
                        optdict = {}
        return self.lines


    def BuildMaximaLines(self):
        if not hasattr(self, 'lines'):
            self.BuildLines()
        maximaout = []
        for line in self.lines:
            curout = line.BuildMaximaLines()
            maximaout.extend(curout)
        self.maximalines = maximaout
        return self.maximalines


    def BuildLatexLines(self, echo=0, replacelist=None, **kwargs):
        self.texlines = []
        for line in self.lines:
            curtex = line.BuildLatexLines(echo=echo, replacelist=replacelist)
            self.texlines.extend(curtex)
        return self.texlines


    def FindReplacePats(self):
        pats = []
        for line in self.lines:
            curpats = line.FindReplacePats()
            pats.extend(curpats)
        self.findpats = pats
        return self.findpats


class MaximaNoOutBlock(MaximaBlock):
    def __init__(self, listin, startline, noout=True, **kwargs):
        MaximaBlock.__init__(self, listin, startline, noout=noout, **kwargs)


class MaximaAnswerBlock(MaximaBlock):
    def __init__(self, listin, startline, answer=False, **kwargs):
        print('MaximaAnswerBlock, answer='+str(answer))
        MaximaBlock.__init__(self, listin, startline, noout=not answer, **kwargs)


class MaximaAnsCommentBlock(MaximaAnswerBlock):
    def BuildLatexLines(self, answer=False, **kwargs):
        self.texlines = []
        if answer:
            self.texlines = self.list
        return self.texlines

    def BuildMaximaLines(self):
        self.maximalines = []
        return self.maximalines

    def FindReplacePats(self):
        return None


class MaximaBlockContBlock(MaximaBlock):
    def BuildLines(self, lineclass=MaximaContLine):
        return MaximaBlock.BuildLines(self, lineclass=lineclass)


    def BuildLatexLines(self, echo=0, replacelist=None, **kwargs):
        self.texlines = ['\\begin{eqnarray}']
        first = 1
        for n, line in enumerate(self.lines):
            curtex = line.BuildLatexLines(echo=echo, replacelist=replacelist)
            if first:
                curtex = [line.replace('=',' & = & ') for line in curtex]
                first = 0
            else:
                self.texlines.append('\\nonumber \\\\')
                curtex[0] = ' & & '+curtex[0]
            self.texlines.extend(curtex)
        self.texlines.append('\\end{eqnarray}')
        return self.texlines


class TexMaximaFile(texpy.TexPyFile):
    """This class represents a Latex file with some Maxima code
    embedded in it."""
    def __init__(self, filepath, envmap=None, folder='temp_eqs', basename='temp_eq_', answer=False, **kwargs):
        """Create a Latex file with embedded Python code."""
        print('TexMaximaFile, answer='+str(answer))
        if envmap is None:
            envmap = {'maxima':MaximaBlock, 'maximano':MaximaNoOutBlock, 'maximaans':MaximaAnswerBlock, 'maximacont':MaximaBlockContBlock,'maximaanscom':MaximaAnsCommentBlock}
        self.envmap = envmap
        self.envstr = '|'.join(self.envmap.keys())
        self.pat = r'^\\('+self.envstr+'){'
        self.p = re.compile(self.pat)
        self.envmap = envmap
        self.path = filepath
        basepath, filename = os.path.split(self.path)
        self.basepath = basepath
        rawlist = pytex.readfile(self.path)
        self.rawlist = copy.copy(rawlist)
        self.lines = copy.copy(self.rawlist)
        self.ind = 0
        self.folder = folder
        self.basename = basename
        self.answer = answer

    def FindReplacePats(self):
        pats = []
        for block in self.blocks:
            curpats = block.FindReplacePats()
            if curpats:
                pats.extend(curpats)
        self.findpats = RemoveDuplicates(pats)
        return self.findpats


    def HasMaxima(self):
        """Check to see if the file actually contains any Python code."""
        oldind = copy.copy(self.ind)
        self.ind = 0
        mybool = self.FindNextEnv()
        self.ind = oldind#reset ind
        return bool(mybool)


    def GetNextEnvNoClear(self):
        """Find the next Maxima environment in self.rawlist, get the
        associated block of code, but leave self.rawlist unmodified."""
        return self.PopNext(clear=False, listname='rawlist')


    def FindBlocks(self):
        print('In FindBlocks, self.answer='+str(self.answer))
        self.blocks = []
        keepgoing = True
        n = 0
        while keepgoing and (n < len(self.rawlist)):
            chunk = self.GetNextEnvNoClear()
            if chunk:
                envkey, codelist = self._CleanChunk(chunk)
                codelist = pytex.CleanList(codelist)
                curclass = self.envmap[envkey]
                curblock = curclass(codelist, self.matchline, folder=self.folder, basename=self.basename, answer=self.answer)
                self.blocks.append(curblock)
            else:
                keepgoing = False
            n += 1
        return self.blocks


    def BuildMaximaScript(self, **kwargs):
        if not hasattr(self, 'blocks'):
            self.FindBlocks(**kwargs)
        maximaout = []
        for block in self.blocks:
            curout = block.BuildMaximaLines()
            maximaout.extend(curout)
        self.maximalines = maximaout
        return self.maximalines


    def MakeMaximaEqnFolder(self):
        if not os.path.exists(self.folder):
            os.mkdir(self.folder)


    def SaveMaximaScript(self, scriptname='temp.mac'):
        if not hasattr(self, 'maximalines'):
            self.BuildMaximaScript()
        self.scriptname = scriptname
        pytex.writefile(self.scriptname, self.maximalines)
        self.MakeMaximaEqnFolder()


    def DeleteMaximaTemp(self):
        """Because Maxima appends its tex output to the files, the tex
        files created by Maxima must be deleted each time."""
        pat = os.path.join(self.folder, self.basename+'*.tex')
        myfiles = glob.glob(pat)
        for curfile in myfiles:
            os.remove(curfile)


    def RunMaxima(self):
        if not hasattr(self, 'scriptname'):
            self.SaveMaximaScript()
        self.DeleteMaximaTemp()
        maxpath_fs = self.scriptname.replace('\\','/')
        maximapath = 'maxima'#this could be hardcoded to something else if maxima wan't in the path
        maximastr = maximapath+' -b '+maxpath_fs
        r,w = os.popen2(maximastr)
        maxo = w.readlines()
        w.close()
        #r.close()
        if pytex.searchlist(maxo,'Incorrect syntax'):
            for line in maxo:
                print(line.strip())


    def SubstituteLatex(self, echo=0, replacelist=None, answer=None):
        """Pop the Maxima blocks and replace them with Latex output."""
        self.ind = 0#reset from self.FindBlocks
        for block in self.blocks:
            chunk = self.PopNext()
            envkey, codelist = self._CleanChunk(chunk)
            codelist = pytex.CleanList(codelist)
            assert codelist == block.list, "Maxima code being replaced doesn't match block.list: codelist="+str(codelist)+" , block.list="+str(block.list)
            curlatex = block.BuildLatexLines(echo=echo, replacelist=replacelist, answer=answer)
            curN = len(curlatex)
            self.lines[self.matchline:self.matchline] = curlatex
            self.ind = self.matchline+curN
        self.latexlist = self.lines
        return self.latexlist


    def ToWLT(self, pathout=None, **kwargs):
        """Dump the file to a wlt file, omitting the body of the text
        (i.e. maxima commands only)."""
        oldind = copy.copy(self.ind)
        if not hasattr(self, 'blocks'):
            self.FindBlocks(**kwargs)
        self.ind = 0
        wltlines = []
        for block in self.blocks:
            chunk = self.PopNext(clear=False, listname='rawlist')
            envkey, codelist = self._CleanChunk(chunk)
            filtcode = stripcodelist(codelist)
            f2code = [item.strip() for item in filtcode]
            wltlines.extend(f2code)
        self.ind = oldind#reset ind
        if pathout is None:
            pne, ext = os.path.splitext(self.path)
            pathout = pne+'.wlt'
        pytex.writefile(pathout, wltlines)
        wltfile = wxmlit.wxmLitFile(pathout)
        wltfile.ToWXM()


class WLTTranslator(texfilemixin.TexFileMixin):
    """This class exists to translate wxMaxima literate programming
    files (.wlt - a simple markup language I made up) into input files
    suitable for TexMaximaFile.  In the wlt files, comments begin with
    a '#' and may contain Latex code.  Uncommented lines are Maxima
    code.  The translation approach will be to simply remove the first
    '#' from commented lines and group the Maxima lines within
    \maxima{ } environments."""
    def __init__(self, filepath):
        self.path = filepath
        if os.path.exists(filepath):
            self.ReadandTranslate()


    def Read(self):
        self.wltlines = pytex.readfile(self.path)


    def Translate(self):
        #need to handle mlabels here and in TexMaximaFile
        linesout = []
        maxopen = False
        noout = False
        cre = re.compile('^\s*#')
        #labelpat = re.compile('^\\s*#\\s*\\\\m*label{(.*?)}')
        curlabel = None
        for line in self.wltlines:
            q = cre.match(line)
            if q:
                if line[1:]=='\\noout':
                    if not noout:#we just switched from out to noout
                        linesout.append('}')
                        maxopen = False
                    noout = True
                elif line[1:8]=='\\mlabel':
                    if not maxopen:
                        linesout.append('\\maxima{')
                        noout = False
                        maxopen = True
                    linesout.append(line[1:])
                else:
                    if maxopen or noout:
                        linesout.append('}')
                        maxopen = False
                        noout = False
                    linesout.append(line[1:])
            elif line:
                if not maxopen:
                    if noout:
                        linesout.append('\\maximano{')
                        noout = False
                    else:
                        linesout.append('\\maxima{')
                maxopen = True
                linesout.append(line)
            elif (not line) and (not maxopen):#this would be an empty line (I think)
                linesout.append(line)
        if maxopen:
            linesout.append('}')
        self.latexlist = linesout
        return self.latexlist


    def ReadandTranslate(self):
        self.Read()
        self.Translate()
