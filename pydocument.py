from scipy import *
#import textfiles
#reload(textfiles)
#import textfiles.latexlist
#reload(textfiles.latexlist)

#from textfiles.latexlist import OutputPath, OpenOutput#, RunLatex

from pytexutils import RunLatex
import txt_mixin
#import textfiles.htmllist
#reload(textfiles.htmllist)

from  IPython.Debugger import Pdb

import pdb

import os, re, shutil, glob, copy

import rwkmisc, rwkos, relpath

import pypres
#reload(pypres)


class Entry(pypres.Line):
    """This class will contain one line of an outline or document file."""
    def __init__(self, linein, p_re=None, sec_re=None, indent=' '*4):
        """Parse a line from an outline or document.  p_re is a
        compiled regular expression used to determine if the line is
        part of an itemize or enumerate list."""
        sec = False
        curlevel = 0
        startind = 0
        enum = False
        star = False
        omit = False
        if p_re is not None:
            q = p_re.match(linein)
        else:
            q = None
        if not q and sec_re is not None:#check if current line is a section
            q = sec_re.match(linein)
            if q:
                sec = True
        if q:
            match = q.group()
            match = match.strip()
            startind = len(match)
            if sec:
                if match[-1] == ':':
                    match = match[0:-1]
                if match[-1] == '*':
                    star = True
                    match = match[0:-1]
            if match[-1] == 'o':
                match = match[0:-1]
                omit = True
            curlevel = len(match)
            #startind = curlevel
            if match.find('#')>-1:
                enum=True
        self.string = linein[startind:].strip()
        if sec and self.string[0]==':':
            self.string = self.string[1:].strip()
        self.level = curlevel
        self.enum = enum
        self.sec = sec
        self.indent = indent
        self.reveal = False
        self.star = star
        self.omit = omit


    def __repr__(self):
        return ','.join([self.string, 'level:'+str(self.level), 'enum:'+str(self.enum)])+'\n'


    def OpenStr(self):
        if self.level == 0 or self.sec:
            return ''
        elif self.enum:
            return '\\begin{enumerate}'
        else:
            return '\\begin{itemize}'

    def CloseStr(self):
        if self.level == 0 or self.sec:
            return ''
        elif self.enum:
            return '\\end{enumerate}'
        else:
            return '\\end{itemize}'

    def ToString(self):
        if self.sec:
            mystr = '\\'+'sub'*(self.level-1)+'section'
            if self.star:
                mystr+='*'
            mystr+='{'+self.string+'}'
            return mystr
        elif self.string =='beginpy_nonum':
            return '\\lstset{style=nonumbers}\n\\begin{lstlisting}{}'
        elif self.string =='endpy':
            return '\\end{lstlisting}'
        outstr = self.indent*self.level
        if self.level > 0:
            outstr +='\item '
        outstr += self.ToLatex()[0]
        #if self.omit:
        #    outstr += ' (not on slides)'
        return outstr


class Document(txt_mixin.txt_file_with_list):
    def ReadFile(self, filename=None):
        if filename is None:
            filename = self.filename
        self.readfile(filename)
        self.rawlist = copy.copy(self.list)
        self.list = [item.strip() for item in self.list]
        #self.list = [item.strip() for item in self.list if item]


    def FindNestLevels(self, pat='^([*#]*)o* ', secpat='^([s]+\\**):', nobody=False):
        """nobody = True keeps all level 0 items out of the final
        document by not putting them in the entrylist."""
        entrylist = []
        p=re.compile(pat)
        ps=re.compile(secpat)
        for item in self.list:
            if item:
                curentry = Entry(item, p, ps)
                if curentry.level > 0 or not nobody:
                    entrylist.append(curentry)
            else:
                entrylist.append(None)
        self.entrylist = entrylist


    def OutlineToSkeleton(self):
        """Turn a document outline into a docuement skeleton, by
        replacing outline markings with section and subsection
        commands."""
        skeleton = []
        replacelist = ['section','subsection','subsubsection']
        N = len(replacelist)
        for item in self.entrylist:
            if item is not None:
                if 0 < item.level <= N:
                    curout = '\\'+replacelist[item.level-1]+'{'+item.str+'}'
                else:
                    curout = item.str
                skeleton.append(curout)
            else:
                skeleton.append('')
        self.skeleton = txt_mixin.txt_file_with_list()
        self.skeleton.list = skeleton
        


    def AddHeader(self):
        if "\\begin{document}" not in self.latexlist.list:
            self.latexlist.AddHeader()


    def HeaderInsert(self, listin):
        self.latexlist.HeaderInsert(listin)

        
    def SkelToFile(self, filename):
        self.skeleton.filename = filename
        self.skeleton.tofile(filename)


    def ToLatex(self, indent=' '*4):
        #print('in ToLatex')
        if not hasattr(self, 'entrylist'):
            self.FindNestLevels()
        texlist = []
        preventry = Entry('')
        openlist = []
        for item in self.entrylist:
            #print('item.string = '+item.string)
            #print('item.ToString() = '+item.ToString())
            if item is not None:
                if item.sec and not preventry.sec:#close everybody
                    closelist = CloseAll(openlist, indent)
                    texlist.extend(closelist)
                    texlist.append('')
                    openlist = [item]
                else:
                    while (item.level != preventry.level) or item.enum != preventry.enum or (preventry.sec and not item.sec):
                        #close and open new itemize or enumerate as necessary
                        if item.level < preventry.level:
                            #for n in range(preventry.level-item.level):
                            curclose = openlist.pop()
                            texlist.append(indent*(curclose.level-1)+curclose.CloseStr())
                            #ind = openlist.index(preventry)
                        elif item.level > preventry.level:
                            texlist.append(indent*(item.level-1)+item.OpenStr())
                            openlist.append(item)
                        elif item.level == preventry.level and ((item.enum != preventry.enum) or (item.sec != preventry.sec)) :
                            #assume we need to close and open when switching from enum to itemize or vice versa
                            curclose = openlist.pop()
                            texlist.append(indent*(curclose.level-1)+curclose.CloseStr())
                            texlist.append(indent*(item.level-1)+item.OpenStr())
                            openlist.append(item)
                        if openlist:
                            preventry = openlist[-1]
                        else:
                            preventry = Entry('')
                texlist.append(item.ToString())
                preventry = item
            else:
                texlist.append('')
        openlist.reverse()
        for item in openlist:
            texlist.append(indent*(item.level-1)+item.CloseStr())
        self.texlist = texlist
        self.latexlist = txt_mixin.txt_file_with_list()
        self.latexlist.list = []
        self.latexlist.list = texlist


    def ToFile(self, filename):
        self.latexlist.filename = filename
        self.latexlist.tofile(filename)


class MechatronicsLab(Document):
    def __init__(self, num, title):
        self.num = num
        self.title = title
        Document.__init__(self)

    def ToLatex(self, indent=' '*4):
        Document.ToLatex(self, indent=indent)
        if self.num:
            rhead = '\\rhead{Lab %s}' % self.num
            titlestr = '\\textbf{\Large Lab %s: %s}'%(self.num, self.title)
        else:
            rhead = '\\rhead{%s}' % self.title
            titlestr = '\\textbf{\Large %s}'%  self.title
        myheader=['\\pagestyle{fancy}','\\lhead{ME 458 Mechatronics}','\\chead{}',rhead, '','\\thispagestyle{plain}', '\\begin{center}',titlestr,'\\end{center}']
        templist = copy.copy(self.latexlist.list)
        self.latexlist.list = myheader+templist


def CloseAll(openlist, indent=' '*4):
    listout = []
    openlist.reverse()
    for item in openlist:
        listout.append(indent*(item.level-1)+item.CloseStr())
    return listout
        

def OutlineToLatexOutline(filepath, runlatex=0, dvi=1, myoutline=None, nobody=False, appendout=False, headerinsert=[]):
    if myoutline is None:
        myoutline = Document()
    myoutline.ReadFile(filepath)
        
    myoutline.FindNestLevels(nobody=nobody)

    myoutline.ToLatex()

    fno, ext = os.path.splitext(filepath)

    ending = '.tex'
    if appendout:
        ending = '_out'+ending
    outname = fno+ending
    myoutline.filename = filepath
    myoutline.latexlist.filename = outname
    myoutline.AddHeader()
    if headerinsert:
        myoutline.HeaderInsert(headerinsert)
    myoutline.ToFile(outname)

    if runlatex:
        finalpath = RunLatex(outname, dvi=dvi)
        return finalpath
    else:
        return outname


def LabOutlineToLatex(filepath, num=None, title=None, runlatex=0, dvi=1):
    myoutline = MechatronicsLab(num, title)
    return OutlineToLatexOutline(filepath, runlatex=runlatex, dvi=dvi, myoutline=myoutline)

