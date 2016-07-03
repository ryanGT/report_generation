"""This module aims to make it easy to make LaTeX documents from
Python.  This is in many way similar to my Python > Maxima > LaTeX
program, but this program will involve rethinking the approach I used
in that work to streamline and improve it.


So, how should this work?  (For now this is as much me thinking about
design as a traditional docstring.)

My immediate need is to take a file like this:

#---------------------------------
from pylab import *
from scipy import *

T = 1.0

fs = 10.0

dt = 1.0/fs

t = arange(0,T,dt)

y = 2.3*sin(4*pi*t)+3.5*cos(12*pi*t)

df = 1.0/T

f = arange(0,fs,df)

Yfft = fft(y)

Aus = real(Yfft)

Bus = -imag(Yfft)

N = len(t)

A = Aus*2.0/N

B = Bus*2.0/N
#---------------------------------

and turn it into

\begin{equation}
T = 1
\end{equation}
.
.
.
\begin{equation}
t = \left[ \begin{array}{cccccccccc} 0 & 0.1 & 0. 2 & 0.3 & 0.4 & 0.5 & 0.6 & 0.7 & 0.8 & 0.9 \end{array} \right]
\end{equation}

or possible

\begin{equation}
t = \begin{bmatrix} 0 & 0.1 & 0. 2 & 0.3 & 0.4 & 0.5 & 0.6 & 0.7 & 0.8 & 0.9 \end{bmatrix}

(using the amsmath package)

mainly this will involve executing each line, finding what is left of
the equals sign, checking its type, and converting it to LaTeX.

I also want to include the option of echoing the Python code in the
LaTeX document using the listings package using something like

\begin{lstlisting}
T = 1.0
\end{lstlisting}


I think this much is fairly straight forward, the trickier part is
when I want to replace variable names with something fancier in LaTeX
like replacing w with \omega.  This has to be done with some care
since you don't want to replace every w, but only the whole word
matches and possibly only in the results, not in the Python code or
any text body.

The text body will come from comments in the Python code:

#This is a line in the final LaTeX document.

with the option of adding Python comments you don't want in the final document:

#!Don't include lines that start with '#!'

There should also be the option of specifiying lines of code you want
executed without their results showing up in the LaTeX document,
possibly using something like:

#beginexclude
temp = 3.4
junk = arange(0,1,0.01)
#endexclude

But how should figures be handled?

There will likely need to be a list of commands whose output is
include in LaTeX such as all imports, figure(), clf(), show(), ...

The lack of an '=' might be a clue as to lines that don't get passed to LaTeX.

It might be cool to have the option of specifying variable whose final
values should be sent to LaTeX by doing something like:

#output: T, dt, Yfft

A list of figures and their possible captions should be made while
processing the Python file.  This would be a great feature.

Eventually, doing all these same things but output to HTML would be
cool as well.


ToDo:
    * different code interweaving options
    * RunLatex method
    * frpatterns stuff

"""

import os, copy, sys, time, subprocess, tokenize, cStringIO, re

import numpy
from scipy import isscalar, shape, imag, real, array, angle

import relpath, pdb

import replacelist

#from IPython.core.debugger import Pdb

#import pytexutils
#reload(pytexutils)
from pytexutils import *

import env_popper
reload(env_popper)

import texfilemixin

import sympy
from IPython.core.debugger import Pdb
#import code_hasher

from var_to_latex import *

label_re = re.compile('label *= *(.*)')

def label_match(line):
    q = label_re.search(line)
    return bool(q)


def LatexMe(line):
    """Test whether or not a line should be include in the ouput
    LaTeX.  For now, only lines with '=' are considered to have
    LaTeX-able output."""
    return HasEqualsSign(line)



def FigWidthHeightStr(dictin):
    mylist = ['width','height']
    for key in mylist:
        if not dictin.has_key(key):
            dictin[key]=''
    if not (dictin['width'] or dictin['height']):
        return 'width=0.75\\textwidth'
    else:
        optstr = ''
    for key in mylist:
        if dictin[key]:
            curopt = key+'='+dictin[key]#i.e. width=4.0in
            if optstr:
                optstr += ', '
            optstr += curopt
    return optstr


def StrToBool(strin):
    if strin is None:
        return False
    if not strin:
        return False
    if strin.lower() == 'false':
        return False
    if strin.lower() == 'true':
        return True
    return int(strin)


def epstopdf(epspath, force=True):
    """Call epstopdf on the file epspath if it exists and the
    equivalent pdf path doesn't exist.  Force calling epstopdf inspite
    of the fact that pdfpath exists with the optional input force."""
    fne, ext = os.path.splitext(epspath)
    pdfpath = fne+'.pdf'
    epspath = fne+'.eps'
    if not os.path.exists(pdfpath) or force:
        if os.path.exists(epspath):
            cmd = 'epstopdf '+epspath
            os.system(cmd)

class empty_class(object):
    def __init__(self,_d={},**kwargs):
        kwargs.update(_d)
        self.__dict__=kwargs


class Result:
    """A class for encapsulating the left and right hand side of a
    Python expression."""
    def __init__(self, lhs, namespace):
        self.string = lhs
        self.namespace = namespace
        self.longarray = False


    def __repr__(self):
        strout = 'pytex.Result instance\n'
        strout += '    string='+self.string+'\n'
        if hasattr(self, 'result'):
            strout += '    result='+str(self.result)+'\n'
        return strout


    def eval(self):
        self.result = eval(self.string, self.namespace)
        self.longarray = IsLongArray(self.result)
        if self.longarray:
            self.Nstr = str(self.result.shape[0])
        return self.result


    def ToLatex(self, **kwargs):
        if not hasattr(self, 'result'):
            self.eval()
        self.latexlist, self.environment = VariableToLatex(self.result, self.string, **kwargs)
        return self.latexlist


    def RHSToLatex(self, **kwargs):
        return NumToLatex(self.result)



class Evaluated_Result(Result):
    """A class for encapsulating the left and right hand side of a
    Python expression that has already been evaluated so that it's rhs
    is known.  I am creating this class to help with for loops."""
    def __init__(self, lhs, rhs, namespace=None):
        self.string = lhs
        self.namespace = namespace
        self.result = rhs
        self.longarray = False


    def eval(self):
        """This method is overridden for compability with the parent
        Result class."""
        self.longarray = IsLongArray(self.result)
        if self.longarray:
            self.Nstr = str(self.result.shape[0])
        return self.result


class Block:
    """This class represents a block of python code that has something
    in common, such as a chunk whose output should not be included in
    the report or a block that represents one figure."""
    def __init__(self, linesin, output=True, comments=False, **kwargs):
        self.lines = linesin
        self.output = output
        self.comments = comments

    def EpstoPdf(self, force=True):
        return None

    def FindLHSs(self):
        self.lhsdict = {}
        for n, line in enumerate(self.lines):
            if HasEqualsSign(line):
                self.lhsdict[n] = lhs(line)
        self.lhslist = self.lhsdict.values()
        return self.lhslist


    def Execute(self, namespace={}, **kwargs):
        """Run the Block of code using Pythons exec function and
        capture the output to self.execdict."""
        self.FindLHSs()
        #self.python = '\n'.join(self.lines)
        #exec self.python in namespace#<--- this is the right approach if the block is a function def or for loop or something.
        #I should probably keep the above and make each unindented line its own block to handle the case of code where the same variable gets defined multiple times as in Bill's code.  Gaels' code hasher may handle this for me.
        lhsinds = self.lhsdict.keys()
        resultdict = {}
        #for ind in lhsinds:
        for n, line in enumerate(self.lines):
            exec line in namespace
            if n in lhsinds:
                lhs = self.lhsdict[n]
                result = Result(lhs, namespace)
                result.eval()
                resultdict[n] = result
        self.resultdict = resultdict
        return self.resultdict


    def ToLatex(self, echo=1, **kwargs):
        """Convert the Block to LaTeX.

        echo determines if and how to interweave the Python code with
        the output in LaTeX.

        echo = 0  - no Python code
        echo = 1  - interweave Python and Latex
        echo = 2  - Python first
        echo = 3  - Python last

        echo = 2 or 3 are actually handled by PythonFile."""
        if not self.output:
            return []
        latexlist = []
        for n, line in enumerate(self.lines):
            if line:
                if line[0]=='#':
                    if len(line)>1 and line[1]!='!':
                        #literal insertion of all comments lines into
                        #the output.
                        #! is a comment that doesn't go in the output
                        temp = line[1:]
                        if temp != '#'*len(temp):
                            latexlist.append(line[1:])
                else:
                    if echo==1:
                        latexlist.append('\\begin{lstlisting}{}')
                        latexlist.append(line)
                        latexlist.append('\\end{lstlisting}')
                    if n in self.resultdict.keys():
                        curres = self.resultdict[n]
                        curlist = curres.ToLatex(**kwargs)
                        latexlist.append('\\begin{'+curres.environment+'}')
                        latexlist.extend(curlist)
                        latexlist.append('\\end{'+curres.environment+'}')
                        if curres.longarray:
                            latexlist.append('\\begin{center}')
                            latexlist.append('(length of $'+curres.string+'$ = '+curres.Nstr+')')
                            latexlist.append('\\end{center}')
        self.latexlist = latexlist
        return self.latexlist

class InputFile(Block):
    def __init__(self,linesin):
        '''
        This block allows the inclusion of other files to be
        preprocessed by pytex.
        '''
        lines = [line.strip() for line in linesin]
        self.lines = []
        for line in lines:
            if line != '':
                self.lines.append(line)
        self.filepath = self.lines[0]
        if os.path.splitext(self.filepath)[1]=='':
            self.filepath = self.filepath+'.tex'

    def Execute(self,namespace={},**kwargs):
        #define the replacelist to make a pretty output
        import replacelist,texpy
        replacelist = replacelist.ReplaceList()
        replacelist.ReadFRFile()

        #define the file/filepath
        inpath = self.filepath
        fno, ext = os.path.splitext(inpath)
        self.outpath = fno+'_out.tex'

        #parse the file and execute the code
        self.tp = texpy.TexPyFile(inpath)
        if not kwargs.has_key('star'):
            kwargs['star']==True
        if not kwargs.has_key('echo'):
            kwargs['echo']=0
        self.tp.Execute(star=kwargs['star'],replacelist=replacelist,echo=kwargs['echo'])
        print self.tp.HasPython(), 'asdfasfas'
        #save the file
        self.tp.SaveLatex(self.outpath,ed=False)

        #append any new potential replacements
        findlist=[]
        findlist.extend(self.tp.FindLHSs())
        replacelist.AppendFRFile(findlist)

    def ToLatex(self,echo,**kwargs):
        latexlist = ['\\input{%s}'%os.path.splitext(self.outpath)[0]]
        return latexlist

class StdoutBlock(Block):
    '''
    A block to capture the stdout of a block of code and
    echo it back in the document.
    '''
    def Execute(self,namespace={},**kwargs):
        '''
        This block of code is executed different than any other block
        of code in that there is no real latex processing done. This
        block of code is executed in namespace and the stdout is captured
        in a StringIO object and returned to be echoed in the document.
        '''
        import StringIO
        codeOut = StringIO.StringIO()
        codeErr = StringIO.StringIO()
        python = '\n'.join(self.lines)
        sys.stdout = codeOut
        sys.stderr = codeErr
        exec python in namespace
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        err = codeErr.getvalue()     #need to throw an exception if err is
        result = codeOut.getvalue()  #anything but "".
        codeOut.close()
        codeErr.close()
        lines = result.split('\n')
        self.lines = lines
        return lines

    def ToLatex(self,**kwargs):
        return self.lines


class FigureBlock(Block):
    def __init__(self, linesin, output=False, comments=False, basepath=''):
        firstline = linesin[0]# get options and filename from here
        self.basepath = basepath
        self.ParseOptions(firstline)
        Block.__init__(self, linesin[1:], output=output, comments=comments)
        self.lhslist = []


    def FindLHSs(self):
        return []

    def EpstoPdf(self, force=True):
        epstopdf(self.figpath, force=force)


    def ParseOptions(self, firstline):
        ind1 = firstline.find('{')
        firstline = firstline[ind1+1:]
        mylist = firstline.split('|')
        keys = ['width','height','caption','label','placestr','center']
        emptyvals = [None]*len(keys)
        self.opts = dict(zip(keys, emptyvals))
        for key in keys:
            curind = findinlist(mylist, key)
            if curind != -1:
                curval = mylist.pop(curind)
                vind = curval.find('=')
                self.opts[key] = curval[vind+1:]
        assert len(mylist)==1, 'After parsing figure options, mylist does not have just the filename left in it  - i.e. len(mylist)!=1.  mylist='+str(mylist)
        outpath = os.path.join(self.basepath, mylist[0])
        if self.opts['center'] is None:
            self.opts['center'] = True#default value
        else:
            self.opts['center'] = StrToBool(self.opts['center'])
        self.opts['filename'] = outpath


    def Execute(self, namespace={}, resave=1, pdf=0, **kwargs):
        """Run the Block of code using Pythons exec function.  If
        resave, save the figure to self.opts['filename']."""
        self.python = '\n'.join(self.lines)
        exec self.python in namespace
        self.resultdict = {}
        filename = self.opts['filename']
        fno, ext = os.path.splitext(filename)
        if not ext:
            ext = '.eps'
        outname = fno+ext
        savestr = 'savefig("'+outname+'")'
        if resave:
            #print('savestr='+savestr)
            exec savestr in namespace
        self.figpath = outname
        return self.resultdict


    def ToLatex(self, pdf=1, **kwargs):
        #the figure path is a full path by default.  This isn't
        #great. Should be relative.
        #
        #whether or not self.opts contains a non-empty caption
        #determines if a floating figure environment is used.
        latexlist = []
        hascaption = bool(self.opts['caption'])
        if hascaption:
            startstr = '\\begin{figure}'
            if self.opts['placestr']:
                startstr += self.opts['placestr']
            latexlist.append(startstr)
        if self.opts['center']:
            latexlist.append('\\begin{center}')
        myoptstr = FigWidthHeightStr(self.opts)
        igline = '\\includegraphics'
        if myoptstr:
            igline +='['+myoptstr+']'
        figpath = self.opts['filename']
        if pdf:
            #print('calling epstopdf')
            epstopdf(figpath)
        #else:
            #print('pdf = '+str(pdf))
        figrelpath = relpath.relpath(figpath, self.basepath)
        figrelpath = figrelpath.replace('\\','/')
        igline += '{'+figrelpath+'}'
        latexlist.append(igline)
        if hascaption:
            latexlist.append('\\caption{'+self.opts['caption']+'}')
            if self.opts['label']:#no sense labeling a non-floating
                                  #figure, so this is a nested if
                latexlist.append('\\label{'+self.opts['label']+'}')
        if self.opts['center']:
            latexlist.append('\\end{center}')
        if hascaption:
            latexlist.append('\\end{figure}')
        self.latexlist = latexlist
        return latexlist


class AnsFigureBlock(FigureBlock):
    def ToLatex(self, answer=False, pdf=1, **kwargs):
        if answer:
            return FigureBlock.ToLatex(self, pdf=pdf, **kwargs)
        else:
            self.latexlist=[]
            return self.latexlist

    def Execute(self, namespace={}, resave=1, pdf=0, answer=False, **kwargs):
        #print('resave='+str(resave))
        #print('answer='+str(answer))
        if answer:
            return FigureBlock.Execute(self, namespace=namespace, resave=resave, pdf=pdf, **kwargs)
        else:
            self.resultdict = {}
            return self.resultdict


class NoOutBlock(Block):
    def __init__(self, linesin, output=False, comments=False, **kwargs):
        if linesin[0].find('#noout{') > -1:
            linesin = linesin[1:]
        Block.__init__(self, linesin, output=output, comments=comments, **kwargs)

    def Execute(self, namespace={}, **kwargs):
        """Run the Block of code using Pythons exec function and
        capture the output to self.execdict."""
        self.cleanlines = [item for item in self.lines if not \
                           label_match(item)]
        self.python = '\n'.join(self.cleanlines)
        exec self.python in namespace


class InnerBlock:
    def __init__(self, codelist, noout=False, label=None, **kwargs):
        if type(codelist) == str:
            codelist = codelist.split('\n')
        self.codelist = codelist
        self.remove_blank_lines_at_start_and_end()
        self.code = '\n'.join(self.codelist)
        self.noout = noout
        self.label = label
##         self.option_list = ['label']
##         for item in self.option_list:
##             setattr(self, item, None)
        self.Parse()


    def remove_blank_lines_at_start_and_end(self):
        if not self.codelist:#don't know if a block with no code ever
                         #happens, but just in case
            return
        while not self.codelist[0]:
            self.codelist.pop(0)
        while not self.codelist[-1]:
            self.codelist.pop()


    def __repr__(self):
        strout = 'pytex.InnerBlock instance\n\n'
        strout +='code:\n'+self.code
        if hasattr(self, 'resultlist'):
            if self.resultlist:
                strout +='\n'
                strout +='resultlist:\n'
                strout +=str(self.resultlist)
        return strout

    def Parse(self):
        nooutlist = ['def','class','for']
        firstline = self.codelist[0]
        for item in nooutlist:
            if firstline.find(item+' ')==0:
                self.noout = True
                break
        keep_going = True
##         while keep_going:
##             keep_going = False
##             firstline = self.codelist[0]
##             for item in self.option_list:
##                 if firstline.find(item) == 0:
##                     pdb.set_trace()
##                     keep_going = True
##                     self.codelist.pop(0)
##                     key, value = firstline.split('=', 1)
##                     value = value.strip()
##                     setattr(self, item, value)
        self.comment = firstline[0]=='#'


    def FindLHSs(self):
        """Find the left hand side arguments of an assignment statement in
        self.code, if one exists."""
        self.lhslist = []
        #if self.noout:
        #    return []
        assert len(self.codelist)==1, 'InnerBlock instance with more than one line and self.noout == False found:'+str(self.codelist)
        #be sure to design in the possibility of muliple lhs arguments
        firstline = self.codelist[0]
        if not HasEqualsSign(firstline):
            if firstline[-1] == ':':#this might not be possible with an InnerBlock
                return []
            else:
                self.lhslist = [firstline]#this allows output a result by putting it on a line by itself, even if it is an expression like a+b
                return self.lhslist
        else:
            lhsstr = lhs(firstline)
            self.lhslist = lhslist(lhsstr)
            return self.lhslist


    def Execute(self, namespace={}, **kwargs):
        """Execute self.code in namespace."""
        self.resultlist = []#if self.noout or self.comment, self.resultlist stays empty
        if not hasattr(self, 'lhlist') or not self.lhslist:
            self.FindLHSs()
        if self.comment:
            return
        exec self.code in namespace
        #if not self.noout:
        self.resultlist = []
        for lhs in self.lhslist:
            result = Result(lhs, namespace)
            result.eval()
            self.resultlist.append(result)
        return self.resultlist



    def ToLatex(self, echo=1, noout=None, replacelist=None, \
                star=False, **kwargs):
        """Convert the Block to LaTeX.

        echo determines if and how to interweave the Python code with
        the output in LaTeX.

        echo = 0  - no Python code
        echo = 1  - interweave Python and Latex
        echo = 2  - Python first
        echo = 3  - Python last

        echo = 2 or 3 are actually handled by PythonFile.

        If replacelist is not None, use frpatterns and search and
        replace to output nice equations instead of raw Python code.
        Those nice equations are output as regular Latex equations
        instead of lstlisting's."""
        if noout is not None:
            self.noout = noout
        if star:
            starstr='*'
        else:
            starstr=''
        latexlist = []
        firstline = self.codelist[0]
        mybool = replacelist is not None
        if self.comment:
            if firstline[1]!='!':
                latexlist.append(firstline[1:])
        else:
            if echo==1:
                echolist = []
                if replacelist is not None:
                    outlist = replacelist.Replace(self.code)
                    if type(outlist)==type('aasdfas'):
                        outlist = [outlist]
                    echolist.append('\\begin{equation'+starstr+'}')
                    echolist.extend(outlist)
                    echolist.append('\\end{equation'+starstr+'}')
                else:
                    echolist.append('\\begin{lstlisting}{}')
                    echolist.append(self.code)
                    echolist.append('\\end{lstlisting}')
                latexlist.extend(echolist)
            if not self.noout:
                for result in self.resultlist:
                    curlist = result.ToLatex(replacelist=replacelist, **kwargs)
                    latexlist.append('\\begin{'+result.environment+starstr+'}')
                    latexlist.extend(curlist)
                    if self.label:
                        print('appending label %s' % self.label)
                        latexlist.append('\\label{%s}' % self.label)
                    latexlist.append('\\end{'+result.environment+starstr+'}')
                    if result.longarray:
                        latexlist.append('\\begin{center}')
                        latexlist.append('(length of $'+result.string+'$ = '+result.Nstr+')')
                        latexlist.append('\\end{center}')
        self.latexlist = latexlist
        return self.latexlist

#p_lhslist = re.compile('(\\s+)lhslist\s*=')
#p_rhslist = re.compile('(\\s+)rhslist\s*=')

p_lhslist = re.compile('lhslist')
p_rhslist = re.compile('rhslist')


class ArbitraryBlock(InnerBlock):
    """This block is for wrapping an arbitrary block of code, that
    might include loops and other complicated calls.  The code must
    define lhslist and rhslist, which determine what goes in the Latex
    output."""
    def __init__(self, codelist, noout=False, **kwargs):
        InnerBlock.__init__(self, codelist, noout=noout, **kwargs)
        mymsg = 'The body of a loop for a pytex.ArbitraryBlock\nmust contain "lhslist" and "rhslist"'
        assert p_lhslist.search(self.code), mymsg
        assert p_rhslist.search(self.code), mymsg


    def Parse(self):
##         mymsg = 'The body of a loop for a pytex.ArbitraryBlock\nmust contain "lhslist" and "rhslist"'
##         assert p_lhslist.search(self.code), mymsg
##         assert p_rhslist.search(self.code), mymsg
        self.comment = False#firstline[0]=='#'


    def Execute(self, namespace={}, **kwargs):
        """Execute self.code in namespace.  lhslist and rhslist will
        be defined in self.code"""
        self.resultlist = []#if self.noout or self.comment, self.resultlist stays empty
        if self.comment:
            return
        exec self.code in namespace
        self.lhslist = eval('lhslist', namespace)
        self.rhslist = eval('rhslist', namespace)
        #if not self.noout:
        self.resultlist = []
        for lhs, rhs in zip(self.lhslist, self.rhslist):
            result = Evaluated_Result(lhs, rhs, namespace)
            self.resultlist.append(result)
        return self.resultlist


    def FindLHSs(self):
        """I am deciding here that ArbitraryBlock and its children
        don't have an lhslist that others need to know about.  That
        assumes that whatever is being put in lhslist is completely
        formatted (probably in Latex)."""
        #return self.lhslist
        return []

p_lhs = re.compile('(\\s+)lhs\s*=')
p_rhs = re.compile('(\\s+)rhs\s*=')

class LoopBlock(ArbitraryBlock):
    def __init__(self, codelist, noout=False, **kwargs):
        if type(codelist) == str:
            codelist = codelist.split('\n')
        self.codelist = codelist
        self.code = '\n'.join(self.codelist)
        mymsg = 'The body of a loop for a pytex.LoopBlock\nmust contain "lhs =" and "rhs ="'
        assert p_lhs.search(self.code), mymsg
        q_rhs = p_rhs.search(self.code)
        assert q_rhs, mymsg
        ws = q_rhs.group(1)
        if ws[0] == '\n':
            ws = ws[1:]
        self.codelist.insert(0,'lhslist = []')
        self.codelist.insert(1,'rhslist = []')
        self.codelist.append(ws+'lhslist.append(lhs)')
        self.codelist.append(ws+'rhslist.append(rhs)')
        self.code = '\n'.join(self.codelist)
        self.noout = noout
        self.Parse()


class PyNoExecuteBlock(InnerBlock):
    def Execute(self, namespace={}, **kwargs):
        self.resultlist = []
        return self.resultlist


    def FindLHSs(self):
        return []


    def ToLatex(self, echo=1, noout=None, replacelist=None, star=False, **kwargs):
        echolist = []
        echolist.append('\\begin{lstlisting}{}')
        echolist.append(self.code)
        echolist.append('\\end{lstlisting}')
        self.latexlist = echolist
        return self.latexlist


class PyAnsCommentBlock(PyNoExecuteBlock):
    def __init__(self, codelist, noout=False, **kwargs):
        if type(codelist) == str:
            codelist = codelist.split('\n')
        self.codelist = codelist
        self.remove_blank_lines_at_start_and_end()
        self.code = '\n'.join(self.codelist)
        self.noout = noout


    def ToLatex(self, echo=1, answer=False, **kwargs):
        self.latexlist = []
        if answer:
            self.noout = False
            self.latexlist = self.codelist
        else:
            self.noout = True#leave self.latexlist completely empty
        return self.latexlist


class PyInLineBlock(InnerBlock):
    def ToLatex(self, **kwargs):#echo=1, noout=None, **kwargs):
        """Convert the Block to LaTeX.  Return a string $...$"""
        assert len(self.resultlist)==1, "PyInLineBlock with more than one result:\n"+str(self.resultlist)
        result = self.resultlist[0]
        reslist = result.ToLatex(**kwargs)
        assert len(reslist)==1, "PyInLineBlock result with a latex list longer than one line:\n"+str(reslist)
        resstr = '$'+reslist[0]+'$'
        self.latexlist = [resstr]
        return resstr


class PyInLineNoExecuteBlock(PyInLineBlock):
    """This block is for putting chunks of code inline in an
    explanation when you don't want to actually execute the code.
    This is especially useful when refering to things like a 'for'
    loop when you want the work for typeset in a special way to point
    out that it is a Python word, but for by itself will generate a
    syntax error."""
    def Execute(self, namespace={}, **kwargs):
        self.resultlist = []
        return self.resultlist


    def ToLatex(self, **kwargs):
        firstline = self.codelist[0]
        assert len(self.codelist)==1, "PyInLineNoExecuteBlock result with a latex list longer than one line:\n"+str(reslist)
        resstr = '\\lstinline!'+firstline+'!'
        self.latexlist = [resstr]
        return resstr


class QuestionBlock(PyInLineBlock):
    def __init__(self, codelist, noout=False, **kwargs):
        if type(codelist) == str:
            codelist = codelist.split('\n')
        firstline = codelist[0]
        if firstline.find('c:') == 0:
            ind = firstline.find('|')
            self.counter = int(firstline[2:ind])
            firstline = firstline[ind+1:]
            #pdb.set_trace()
            codelist.pop(0)
            codelist.insert(0, firstline)
        else:
            self.counter = None
        self.codelist = codelist
        self.code = '\n'.join(self.codelist)
        self.noout = noout
        self.Parse()


    def ToLatex(self, handout=False, outline=True, count=None, **kwargs):#echo=1, noout=None, **kwargs):
        """Convert the Block to LaTeX.  Return a string $...$"""
        if self.counter is None:
            if count is not None:
                self.counter = count
            else:
                self.counter = 1
        assert len(self.resultlist)==1, "PyInLineBlock with more than one result:\n"+str(self.resultlist)
        result = self.resultlist[0]
        reslist = result.ToLatex(**kwargs)
        lhs = result.string
        rhs = result.RHSToLatex(**kwargs)
        assert len(reslist)==1, "PyInLineBlock result with a latex list longer than one line:\n"+str(reslist)
        if handout:
            resstr = '$'+lhs+' = $'
        elif outline:
            resstr = '$'+lhs+' = '+rhs+'$'
        else:
            resstr = '$'+lhs+' = $\only<'+str(self.counter)+'| handout:0>{?}\only<'+str(self.counter+1)+'-| handout:0>{$'+rhs+'$}'
        self.counter += 1
        self.latexlist = [resstr]
        return resstr


class OuterBlock:
    """This class will be used to handle my initial parsing of the
    Python code into figure blocks, noout blocks, answer blocks, and
    regular blocks."""
    def __init__(self, linesin, noout=False, comments=False, **kwargs):
        self.lines = linesin
        self.noout = noout
        self.comments = comments
        self.kwargs = kwargs


    def _FindRawBlocks(self):
        """Break the code chunk associated with the OuterBlock
        instance into smaller chunks, making sure that things like for
        loops, function definitions and classes stay together as one
        chunk."""
        #myhasher = code_hasher.CodeHasher(iter(self.lines))
        #blockgen = myhasher.itercodeblocks()
        #self.rawblocks = [block for block in blockgen]
        #self.cleanblocks = [block.string.strip() for block in self.rawblocks]
        self.hasher = MyHasher(self.lines)
        self.rawblocks = self.hasher.Hash()


    def CleanBlocks(self):
        #How should whitespace in a python file be handled?
        self.cleanblocks = [CleanList(item) for item in self.rawblocks]
        return self.cleanblocks


    def FindBlocks(self):
        self._FindRawBlocks()
        self.CleanBlocks()
        self.blocks = []

        label = None
        for item in self.cleanblocks:
            q = label_re.search(item[0])
            if q:
                label  = q.group(1)
                item.pop(0)
            if item:
                curblock = InnerBlock(item, noout=self.noout, \
                                      label=label)
                self.blocks.append(curblock)
                label = None


    def Execute(self, namespace={}, **kwargs):
        """Call the Execute methods of all the blocks in self.blocks."""
        if not hasattr(self, 'blocks'):
            self.FindBlocks()
        for block in self.blocks:
            block.Execute(namespace=namespace, **kwargs)


    def ToLatex(self, echo=False, replacelist=None, star=False, \
                **kwargs):
        """Call the ToLatex methods of all the blocks in self.blocks."""
        self.latexlist = []
        for block in self.blocks:
            curlist = block.ToLatex(echo=echo, replacelist=replacelist, \
                                    star=star, **kwargs)
            self.latexlist.extend(curlist)
        return self.latexlist


    def EpstoPdf(self, force=True):
        return None


    def FindLHSs(self):
        self.lhslist = []
        for block in self.blocks:
            self.lhslist.extend(block.FindLHSs())
        return self.lhslist


class EchoBlock(OuterBlock):
    def __init__(self, linesin, **kwargs):
        if linesin[0] == '#pyecho':
            linesin.pop(0)
        OuterBlock.__init__(self, linesin, **kwargs)


    def ToLatex(self, **kwargs):
        kwargs['echo'] = 1
        empty_list = replacelist.ReplaceList([])
        if kwargs.has_key('replacelist'):
            if kwargs['replacelist'] is None:
                kwargs['replacelist'] = empty_list
        else:
            kwargs['replacelist'] = empty_list
        return OuterBlock.ToLatex(self, **kwargs)


class AnswerBlock(OuterBlock):
    def __init__(self, linesin, noout=True, **kwargs):
        if linesin[0].find('#answer{') > -1:
            linesin = linesin[1:]
        OuterBlock.__init__(self, linesin, noout=noout, **kwargs)


    def ToLatex(self, echo=1, answer=False, **kwargs):
        """Call the ToLatex methods of all the blocks in self.blocks."""
        self.latexlist = []
        #print('In AnswerBlock, answer='+str(answer))
        #print('echo='+str(echo))
        if answer:
            self.noout = False
            for block in self.blocks:
                curlist = block.ToLatex(echo=echo, noout=self.noout, **kwargs)
                self.latexlist.extend(curlist)
        else:
            self.noout = True#leave self.latexlist completely empty
        return self.latexlist



class BlockParser:
    """This class takes a Python file and breaks it into Block
    instances.  For now, it does not handle nested blocks."""
    def __init__(self, linesin=[], blockmap=None, basepath=''):
        if blockmap is None:
            blockmap = {'answer':AnswerBlock, 'noout':NoOutBlock, \
                        'figure':FigureBlock}
        self.blockmap = blockmap
        self.lines = linesin
        self.basepath = basepath
        #if linesin:
        #    self.Parse()


    def Parse(self, answer=False):
        """Break a list of Python code into Blocks where each block is
        assumed to begin with '#blockname{' and end with '#}', where
        blockname is an item in self.blockmap.keys()."""
        linelist = MyList(copy.copy(self.lines))
        startdict = {}
        for key in self.blockmap.keys():
            curpat = '#'+key+'{'
            curstarts = linelist.findall(curpat, forcestart=1)
            vallist = [key]*len(curstarts)
            curdict = dict(zip(curstarts, vallist))
            startdict.update(curdict)

        startlist = startdict.keys()
        startlist.sort()
        endlist = linelist.findall('#}', forcestart=1)
        endlist.sort()

        blocklist = []
        curstart = 0

        for nextstart, nextend in zip(startlist, endlist):
            if nextstart != curstart:
                #then there is a block of normal code between environments
                normalblock = OuterBlock(linelist[curstart:nextstart], basepath=self.basepath)
                blocklist.append(normalblock)
            curkey = startdict[nextstart]
            curclass = self.blockmap[curkey]
            curblock = curclass(linelist[nextstart:nextend], basepath=self.basepath)
            blocklist.append(curblock)
            curstart = nextend+1
        if curstart < len(linelist):
            lastblock = OuterBlock(linelist[curstart:])
            blocklist.append(lastblock)
        self.blocklist = blocklist
        return self.blocklist


pytex_def_map = {'fig':FigureBlock, 'body':OuterBlock, \
                 'no':NoOutBlock, 'echo':EchoBlock}



class PythonFile(texfilemixin.TexFileMixin):
    def __init__(self, filepath):
        """Create a PythonFile that will be executed and its output
        turned into a LaTeX document."""
        self.path = filepath
        basepath, filename = os.path.split(self.path)
        self.basepath = basepath
        rawlist = readfile(self.path)
        self.rawlist = rawlist


    def Execute(self, **kwargs):
        #self.resultdict = {}
        self.namespace = {}
        for block in self.blocks:
            block.Execute(namespace=self.namespace, **kwargs)
            #self.resultdict.update(block.resultdict)


    def ToBlocks(self, blockmap=None):
##         self.blockparser = BlockParser(self.rawlist, \
##                                        blockmap=blockmap, \
##                                        basepath=self.basepath)
##         self.blocks = self.blockparser.Parse()
        self.popper = env_popper.python_report_popper(self.rawlist, \
                                               map_in=pytex_def_map)
        self.blocks = self.popper.Execute()


    def ToListing(self):
        mylist = []
        mylist.append('\\begin{lstlisting}{}')
        for block in self.blocks:
            mylist.extend(copy.copy(block.lines))
        mylist.append('\\end{lstlisting}')
        self.listing = mylist
        return mylist


    def ToLatex(self, echo=False, **kwargs):
        #print('fix me')
        mylatexlist = []
        #Pdb().set_trace()
        if echo == 2:
            mylatexlist.append('\\pagebreak')
            mylatexlist.append('\\section*{Python Code}')
            mylatexlist.extend(self.ToListing())
        for block in self.blocks:
            curlatex = block.ToLatex(echo=echo, **kwargs)
            mylatexlist.extend(curlatex)
        if echo == 3:
            mylatexlist.append('\\pagebreak')
            mylatexlist.append('\\section*{Python Code}')
            mylatexlist.extend(self.ToListing())
        self.latexlist = mylatexlist
        return self.latexlist


    def FindLHSs(self):
        self.lhslist = []
        for block in self.blocks:
            self.lhslist.extend(block.FindLHSs())
        return self.lhslist


    def EpstoPdf(self, force=True):
        for block in self.blocks:
            block.EpstoPdf(force=force)



if __name__ == '__main__':
    #mydir = '/home/ryan/siue/classes/mechatronics/2007/test2'
    #myfile = 'solution.py'
    #mypath = os.path.join(mydir, myfile)
    #mypath = '/home/ryan/siue/classes/mechatronics/2007/ExraCreditProblems/larry.py'
    exdir = '/home/ryan/siue/classes/356/2008/lectures/chapter_4/python_examples'
    #exdir = '~/pythonutil/test/'
    myfile = 'ogata_example_4_3.py'
    mypath = os.path.join(exdir, myfile)
    mypyfile = PythonFile(mypath)
    mypyfile.ToBlocks()
    #Pdb().set_trace()
    mypyfile.Execute()
    mypyfile.ToLatex(echo=3, answer=True)
    mypyfile.AddHeader()
    mypyfile.SaveLatex()
    mypyfile.RunLatex(dvi=1, openviewer=1)
    #mypyfile.RunLatex(dvi=0, openviewer=1)
