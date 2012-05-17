import os, copy, sys, time, pdb, \
       subprocess, tokenize, cStringIO, re, glob

import numpy
from scipy import isscalar, shape, imag, real, array

import rwkos, rwkmisc

import relpath

#from IPython.Debugger import Pdb
from IPython.core.debugger import Pdb

floatre = re.compile(r'[+-]*\d*\.*\d+')

ws = ' '*4

def cleanLatexOutputFiles(pathto,basename,exts=['log','aux','out']):
    for ext in exts:
        curfile = basename+'.'+ext
        curpath = os.path.join(pathto,curfile)
        if os.path.exists(curpath):
            os.unlink(curpath)

def clean_dir(folder_path, exts=['*.log','*.aux','*.out']):
    for ext in exts:
        pat = os.path.join(folder_path, ext)
        myfiles = glob.glob(pat)
        for curpath in myfiles:
            os.remove(curpath)

def OptionsDictFromList(listin, optdict=None):
    loners = []
    if optdict is None:
        optdict = {}
    for item in listin:
        item = item.strip()
        if item.find(':') > -1:
            key, val = item.split(':',1)
            optdict[key] = val
        else:
            loners.append(item)
    return optdict, loners


def break_at_pipes(string_in):
    listout = string_in.split('|')
    return listout


def StrToDict(strin):
    mylist = strin.split('|')
    mydict = {}
    for item in mylist:
        if ':' in item:
            key, val = item.split(':',1)
            mydict[key] = val
        else:
            mydict[item] = 1
    return mydict


def RemoveDuplicates(listin):
    vals = range(len(listin))
    mydict = dict(zip(listin, vals))
    uniquekeys = mydict.keys()
    inds = mydict.values()
    #try and return the filtered list in the orginial order
    otherdict = dict(zip(inds, uniquekeys))
    inds.sort()
    outlist = []
    for ind in inds:
        outlist.append(otherdict[ind])
    return outlist
    


def CleanList(listin):
    temp = None
    while not temp:
        temp = listin.pop()
    listin.append(temp)
    temp = None
    while not temp:
        temp = listin.pop(0)
    listin.insert(0,temp)
    return listin


def findinlist(listin, searchstr):
    found = -1
    for n, line in enumerate(listin):
        if line.find(searchstr) > -1:
            found=n
            break
    return found


def findinlistre(listin, pat):
    found = -1
    p = re.compile(pat)
    for n, line in enumerate(listin):
        q = p.search(line)
        if q:
            found=n
            break
    return found
    
    
def searchlist(listin,searchstr):
    myind = findinlist(listin, searchstr)
    return bool(myind != -1)


def splittolist(pathstr):
    listout=[]
    rest=copy.copy(pathstr)
    rest, curent=os.path.split(rest)
    if len(curent)>0:
        listout[:0]=[curent]
    while (len(rest)*len(curent))>0:
        rest, curent=os.path.split(rest)
        if len(curent)>0:
            listout[:0]=[curent]
    if len(rest)>0:
        listout[:0]=[rest]
    return listout

    
def amiLinux():
    platstr=sys.platform
    platstr=platstr.lower()
    if platstr.find('linu')>-1:
        return 1
    else:
        return 0


def walkuplist(pathstr):
    sep=os.sep
    mylist=splittolist(pathstr)
    if not amiLinux():
        while mylist[0][-1]==sep:
            mylist[0]=mylist[0][0:-1]
    listout=[]
    NN = len(mylist)
    for n in range(1,NN):
        curpath = sep.join(mylist[0:NN-n])
        listout.append(curpath)
    if os.path.isdir(pathstr):
        listout.insert(0,pathstr)
    return listout


def FindinPath(filename):
    pathlist=sys.path
    outpath=''
    for curpath in pathlist:
        temppath=os.path.join(curpath,filename)
        if os.path.exists(temppath):
            outpath=temppath
            break
    return outpath


def FindWalkingUp(filename, pathstr=None, includesys=False):
    if pathstr is None:
        pathstr, filename = os.path.split(filename)
        if not pathstr:
            pathstr = os.getcwd()
    mypathlist = walkuplist(pathstr)
    found = 0
    if includesys:
        fullpathlist = mypathlist+os.sys.path
    else:
        fullpathlist = mypathlist
    for path in fullpathlist:
        curfp = os.path.join(path,filename)
        if os.path.exists(curfp):
            found = 1
            fp = curfp
            break
    if found:
        return fp
    else:
        return None
    

def readfile(pathin, strip=False, rstrip=True, verbosity=0):
    goodpath = None
    if os.path.exists(pathin):
        goodpath = pathin
    else:
        mypath = FindWalkingUp(pathin)
        if mypath:
            goodpath = mypath
        else:
            junk, filename = os.path.split(pathin)
            mypath=FindinPath(filename)
            if mypath:
                goodpath = mypath
            
    if goodpath:
        if verbosity > 0:
            print('found file:'+goodpath)
        f=open(goodpath,'r')
    else:
        raise StandardError, "Could not find "+pathin+" in sys.path"
    listin=f.readlines()
    f.close()
    if strip:
        listout = [line.strip() for line in listin]
    elif rstrip:
        listout = [line.rstrip() for line in listin]
    else:
        listout = listin
    return listout


def add_newlines(listin):
    listout = []
    for line in listin:
        if not line:
            listout.append('\n')
        elif line[-1]!='\n':
            listout.append(line+'\n')
        else:
            listout.append(line)
    return listout


def writefile(pathin, listin, append=False):
    if append and os.path.exists(pathin):
        openstr = 'ab'
    else:
        openstr = 'wb'
    f = open(pathin, openstr)
    listout = add_newlines(listin)
    f.writelines(listout)
    f.close()


def HasEqualsSign(line):
    eqind = line.find('=')
    poundind = line.find('#')
    if eqind > -1:
        if poundind > -1:
            return bool(eqind < poundind)
        else:
            return True
    else:
        return False


def filterlhs(lhsin):
    """I had some problems with just grabbing everything to the left
    of the equals sign with Maxima output.  Sometimes there are very
    complicated expressions over there and I just want simple
    variables.  If lhsin is complicated, return an empty string."""
    badlist = ['\\left','\\right','\\frac','\\displaystyle','\\begin','\\end','\\,']
    for item in badlist:
        if item in lhsin:
            return ''
    if floatre.match(lhsin.strip()):#we aren't going to replace floating point or integer lhs's
        return ''
    return lhsin

    
def lhs(line):
    """Find the left hand side of a line with an equals sign."""
    lineout = line.strip()
    ind = lineout.find('=')
    if ind==-1:
        return ''
    myout = lineout[0:ind]
    myout = myout.strip()
    myout = filterlhs(myout)
    return myout
    


def lhslist(strin):
    """Break the lhs string into a list of arguments."""
    mylist = strin.split(',')
    mylist = [item.strip() for item in mylist]
    return mylist


def _close_itemize(prev_level, cur_level):
    outlist = []
    num_to_close = prev_level-cur_level
    extra_ws = ws*cur_level
    for n in range(num_to_close):
        cur_ws = (num_to_close-n-1)*ws+extra_ws
        outlist.append(cur_ws+'\\end{itemize}')
    return outlist


def objlist_to_latex(objlist, mapper, baselevel=0, \
                     startstr='\\begin{itemize}'):
    """This function converts a list of objects to LaTeX.  The objects
    most likely come from a nested list pyp file and some sort of
    pyp_parser object."""
    outlist = []
    prev_level = baselevel
    for item in objlist:
        cur_ws = ws*(item.level-1)
        if item.level < prev_level and (prev_level > baselevel):
            if item.level < baselevel:
                stop_level = baselevel
            else:
                stop_level = item.level
            close_list = _close_itemize(prev_level, stop_level)
            outlist.extend(close_list)
        if item.level <= baselevel:
            #if item.level <= baselevel:
            if mapper.has_key(type(item)):
                my_class = mapper[type(item)]
                my_instance = my_class(item)
                outlist.extend(my_instance.to_latex())
            else:
                outlist.append(item.rawline)#need to preserve leading whitespace for Python code in lstlistings
##             else:
##                 outlist.append(item.string)
        if item.level > prev_level and item.level > baselevel:
            outlist.append(cur_ws+startstr)
        if item.level >= (baselevel+1):
            outlist.append(cur_ws+ws+'\\item '+item.string)
        prev_level = item.level

    #close any open itemize's:
    if prev_level != baselevel:
        close_list = _close_itemize(prev_level, baselevel)
        outlist.extend(close_list)
    return outlist


def FindReplacementCandidates(listin):
    if not listin:
        return []
    if type(listin)==list or type(listin)== tuple:
        myinput = ' '.join(listin)
    elif type(listin)==str:
        myinput = listin
    else:
        raise TypeError, "I don't know what to do with input of type:"+str(type(listin))+"\nlistin="+str(listin)
    findpats = []
    mylhs = lhs(myinput)
    if mylhs:
        findpats.append(mylhs)
    p = re.compile(r'{\\it .*?}')
    itlist = p.findall(myinput)
    findpats.extend(itlist)
    findpats = RemoveDuplicates(findpats)
    return findpats


def RunLatex(filepath, dvi=0, openviewer=False, sourcespecials=True, log=None, **kwargs):
    """Call Latex with file filename.  If dvi is True, regular Latex
    is called, otherwise pdflatex is called.  If openviewer is True,
    subprocess is called to open the file using either xdvi or
    acroread (note that this may not work on all platforms)."""
    folder, filename = os.path.split(filepath)
    curdir = os.getcwd()
    print('curdir='+curdir)
    print('folder='+folder)
    if dvi:
        latexcmd='latex'
        viewerext='.dvi'
        viewer='kdvi'
    else:
        latexcmd='pdflatex'
        viewerext='.pdf'
        viewer='acroread'
    if sourcespecials:
        latexstr2=latexcmd+' --src-specials -interaction=nonstopmode '+filename
        opt_str = '--src-specials -interaction=nonstopmode '+filename
    else:
        latexstr2=latexcmd+' -interaction=nonstopmode '+filename
        opt_str = '-interaction=nonstopmode '+filename
    tl1=time.time()
    try:
        if folder:
            os.chdir(folder)
        #r,w=os.popen2(latexstr2)
        #texout=w.readlines()
        p = subprocess.Popen(latexstr2, shell=True, \
                             stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        output, errors = p.communicate()
        texout = output.split('\n')
        #w.close()
        #r.close()
        if searchlist(texout,'LaTeX Error') or searchlist(texout,'LaTeX Warning') or searchlist(texout,'!'):
            for line in texout:
                print(line.strip())
        if searchlist(texout,'Label(s) may have changed'):
            print('Running LaTeX a second time.')
            p = subprocess.Popen(latexstr2, shell=True, \
                                 stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            output, errors = p.communicate()
            texout = output.split('\n')
            #r,w,e=os.popen3(latexstr2)
            #texout=w.readlines()
            #w.close()
            #texe=e.readlines()
            #e.close()
            #r.close()
    finally:
        os.chdir(curdir)
    tl2=time.time()
    print('Run LaTeX time='+str(tl2-tl1))
    outfno,ext=os.path.splitext(filepath)
    if openviewer:
        pid=subprocess.Popen([viewer,outfno+viewerext]).pid
    return outfno+viewerext


def OpenOutput(outputpath, dvi=None, debug=1, kpdf=False):
    if dvi is None:
        pne, ext = os.path.splitext(outputpath)
    elif dvi:
        ext = '.dvi'
    else:
        ext = '.pdf'

    if rwkos.amiLinux():
        cmds={'.dvi':'kdvi %s','.pdf':'acroread %s'}
        if kpdf:
            cmds['.pdf'] = 'kpdf %s'
    else:
        cmds={'.dvi':'yap -1 %s','.pdf':'AcroRd32 %s'}
    mycmd=cmds[ext]% outputpath
    if debug > 0:
        rwkmisc.PrintToScreen(['mycmd'],locals())
    if rwkos.amiLinux():
        os.system(mycmd + ' &')
    else:
        subprocess.Popen(mycmd)

        

class MyTokenizer:
    """Class for converting a chunk of Python code to a list of blocks
    that should stay together."""
    def __init__(self, codein):
        if type(codein)==list:
            codein = ''.join(codein)
        a = cStringIO.StringIO(codein)
        self.tokgen = tokenize.generate_tokens(a.readline)

    def Tokenize(self):
        listout = []
        prevrow = -1
        for toktype, tokstring, (srow, scol), (erow, ecol), curline in self.tokgen:
            if srow!=prevrow:
                listout.append(curline)
            prevrow = srow
        self.list = listout
        return self.list
        

class MyList:
    def __init__(self, listin):
        self.list = listin
        self._MapMethods()


    def _MapMethods(self):
        mylist = ['__getslice__','__setitem__', '__setslice__', 'extend','__getitem__', '__len__', '__contains__', '__delitem__', '__delslice__']
        for item in mylist:
            setattr(self, item, getattr(self.list, item))


    def findall(self,pattern,forcestart=0):
        linenums=[]
        for line,x in zip(self.list, range(len(self.list))):
            ind=line.find(pattern)
            if forcestart:
                if ind==0:
                    linenums.append(x)
            else:
                if ind >- 1:
                    linenums.append(x)
        return linenums


    def findallre(self, pattern, match=1):
        """Use regular expression module re to find all lines with
        pattern.

        If match=1 or True, then a match is preformed, anchoring the
        search to the begining of each line.  match=0 or False calls
        re.search which matches pattern anywhere in the current line."""
        p=re.compile(pattern)
        linenums=[]
        for line,x in zip(self.list, range(len(self.list))):
            if match:
                m=p.match(line)
            else:
                m=p.search(line)
            if m:
                linenums.append(x)
        return linenums  


class MyHasher:
    def __init__(self, codein):
        self.code = MyList(codein)


    def Hash(self):
        pat = '^[a-z]|[A-Z]|#'
        self.rawblocks = []
        inds = self.code.findallre(pat)
        if inds:#if there are no inds, the block is probably just one empty line
            prevind = inds.pop(0)
            for ind in inds:
                curblock = self.code[prevind:ind]
                self.rawblocks.append(curblock)
                prevind = ind
            self.rawblocks.append(self.code[prevind:])
        return self.rawblocks
            
