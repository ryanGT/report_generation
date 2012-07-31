from scipy import *
#import textfiles
#reload(textfiles)
#import textfiles.latexlist
#reload(textfiles.latexlist)

#import textfiles.htmllist
#reload(textfiles.htmllist)
import txt_mixin
from pytexutils import RunLatex

#from IPython.core.debugger import Pdb

import os, re, shutil, glob, pdb

import rwkmisc, rwkos, relpath
#reload(rwkos)

import texfilemixin
import copy


def break_at_pipes(matchobj):
    core = matchobj.group(1)
    listout = core.split('|')
    return listout


def CreateHTMLLink(filepath, linktext=''):
    if not linktext:
        linktext=filepath
    return '<A HREF="%s">%s</A>'%(filepath, linktext)

def CreateSlideName(slidenum, basename='slide',fmt='%0.3d'):
    return basename+fmt%slidenum+'.html'


def ImageMajickResize(pathin, maxw=1200, maxh=1200, append='_w_1200', sizethresh=100000):
    pne, ext = os.path.splitext(pathin)
    badlist = ['eps','pdf']
    checkext = ext.lower()[1:]
    if checkext in badlist:
        ext = '.png'
        pathin = pne+ext
    #    return pathin
    pathout = pne+append+ext
    mysize = os.path.getsize(pathin)
    if mysize <= sizethresh:
        return pathin
    else:
        if not os.path.exists(pathout):
            temppath = rwkos.checklower(pathout)
            if temppath:
                return temppath
            else:
                cmd = 'convert '+pathin + ' -resize ' + str(maxw) + 'x' + str(maxh) + ' ' + pathout
                print cmd
                os.system(cmd)
        return pathout

def JPEG2EPS(pathin):
    pne, ext = os.path.splitext(pathin)
    if ext.lower()!='.jpg':
        return pathin
    epspath = pne + '.eps'
    if not os.path.exists(epspath):
        cmd = 'jpeg2ps ' + pathin + ' > ' + epspath
        os.system(cmd)
    return epspath


def StringToLatexDim(stringin, post='\\textwidth'):
    try:
        dim = float(stringin)
        strout = str(dim)+post
    except:
        strout = stringin
    return strout


zerolist = ['0','None','none','NONE']


def ParseHeightWidth(string, percent=False, fmt='%d'):
    if string in zerolist:
        return '0'
    if percent:
        try:
            myfloat = float(string)
            if myfloat <= 1.0:
                myfloat = 100*myfloat
            return fmt%myfloat
        except:
            return string
    else:
        return string


def DictToHeightWidth(mydict, percent=False):
    """Try to discern the desired figure height and width based on
    height and width strings in a dictionary.

    If percent is True, try turning widht and height into floats and
    multiply by 100 if they are less than or equal to 1.

    Returns strings for width and height"""
    if mydict.has_key('width'):
        wstr = mydict['width']
        w = ParseHeightWidth(wstr, percent=percent)
    else:
        w = ''
    if mydict.has_key('height'):
        hstr = mydict['height']
        h = ParseHeightWidth(hstr, percent=percent)
    else:
        h = ''
    return w, h


def WidthAndHeightToHTMLStyleTag(width, height=None, units='%'):
    outstr = ''
    if width:
        outstr += 'width: %s'%width+units+';'
    if height:
        outstr += 'height: %s'%height+units+';'
    return outstr


def DictToLatexFigString(mydict, mypath):
    outstr = '\\includegraphics['
    if mydict.has_key('height'):
        height = mydict['height']
        hstr = StringToLatexDim(height, post='\\textheight')
        outstr += 'height='+hstr
        mydict.pop('height')
    else:
        width = mydict['width']
        wstr = StringToLatexDim(width)
        outstr += 'width='+wstr
        mydict.pop('width')
    for key, val in mydict.iteritems():
        if key != 'center':
            outstr += ', ' + key + '=' + val
    outstr += ']{'+mypath+'}'
    falselist = ['false','False','0']
    if mydict['center'] in falselist:
        mydict['center'] = False
    if mydict['center']:
        outstr = '\\begin{center} ' + outstr +' \\end{center}'
    return outstr


def OptionsDictFromList(listin, optdict=None):
    if optdict is None:
        optdict = {}
    for item in listin:
        item = item.strip()
        if item.find(':'):
            key, val = item.split(':',1)
            optdict[key] = val
    return optdict


def LatexEqnReplace(matchobj):
    body = matchobj.group(1)
    return '\\begin{equation}\n'+body+'\\end{equation}'


def LatexEqnsReplace(matchobj):
    body = matchobj.group(1)
    return '\\begin{equation*}\n'+body+'\\end{equation*}'


def LatexFigReplace(matchobj, scale=False, epstopdf=False):
    mylist = break_at_pipes(matchobj)
    temppath = mylist[-1]
    print('temppath='+temppath)
    #mypath = relpath.relpath(temppath, os.getcwd())
    mypathout, ext = os.path.splitext(temppath)
    print('temppath='+temppath)
    if not ext:
        extlist = ['.eps','.pdf','.jpg','.png']
        found = 0
        for item in extlist:
            if os.path.exists(temppath+item):
                mypath = temppath
                found = True
                break
    else:
        mypath = rwkos.FindFullPath(temppath)
        found = os.path.exists(mypath)
        print('mypath='+mypath)
    if not found:
        print('could not find the path '+temppath)
        mypath = temppath
    else:
        if ext:
            pathne, ext = os.path.splitext(mypath)
            skiplist = ['.eps','.pdf']
            if ext not in skiplist:
                if scale:
                    mypath = ImageMajickResize(mypath)
                if epstopdf:
                    epspath = JPEG2EPS(mypath)
                mypath = mypath.replace('\\','/')#latex paths are hardcoded to /
                mypath = mypath.replace('//','/')

    keys = ['width','center','height']
    vals = ['0.75\\textwidth',True]#default values
    mydict = {}#dict(zip(keys,vals))
    for item in mylist:
        item = item.strip()
        for key in keys:
            if item.find(key+':')==0:
                junk, val = item.split(':',1)
                mydict[key] = val
    if not (mydict.has_key('width') or mydict.has_key('height')):
        mydict['width']='0.75\\textwidth'
    if not mydict.has_key('center'):
        mydict['center']=True
    outstr = DictToLatexFigString(mydict, mypathout)
    return outstr


def HTMLFigReplace(matchobj):
    mylist = break_at_pipes(matchobj)
    temppath = mylist.pop()
    #mypath = relpath.relpath(temppath, os.getcwd())
    abs=False
    if 'abs' in mylist:
        abs=True
    mypath = rwkos.FindFullPath(temppath)
    #print('temppath='+temppath)
    #print('mypath='+mypath)
    assert mypath, 'could not find the path '+temppath
    mypath = ImageMajickResize(mypath)
    myrelpath = relpath.relpath(mypath)
    myrelpath = myrelpath.replace('\\','/')#latex paths are hardcoded to /
    myrelpath = myrelpath.replace('//','/')
    mydict = OptionsDictFromList(mylist)
    w, h = DictToHeightWidth(mydict, percent=True)
    if not w and not h:
        w=100
    if w=='0':
        w = None#use '0' to denote that no width setting is desired as opposed to a default of 100%
    stylestr = WidthAndHeightToHTMLStyleTag(w, h)
    outstr = HTMLIMageString(myrelpath, stylestr=stylestr)
    return outstr


def pathReplace(matchobj):
    return '\\path{'+matchobj.group(1)+'}'


def BreakLink(matchobj):
    core = matchobj.group(1)
    if core.find('|') > -1:
        linktext, dest = core.split('|',1)
    else:
        linktext = core
        dest = core
    return linktext, dest


def LinkLatexReplace(matchobj):
    linktext, dest = BreakLink(matchobj)
    linktext = linktext.replace('_','\\_')
    return '\\href{%s}{\\color{darkblue}%s}'%(dest, linktext)

def RunLinkLatexReplace(matchobj):
    linktext, dest = BreakLink(matchobj)
    linktext = linktext.replace('_','\\_')
    return '\\href{run:%s}{\\color{darkblue}%s}'%(dest, linktext)


def LinkHTMLReplace(matchobj):
    linktext, dest = BreakLink(matchobj)
    return CreateHTMLLink(dest, linktext)

def RunHTMLReplace(matchobj):
    linktext, dest = BreakLink(matchobj)
    rundest = rwkos.FindFullPath(dest)
    return CreateHTMLLink(rundest, linktext)


def MakeBat(dest, reportdir=''):
    mypath = os.path.join(reportdir, dest)
    path, filename = os.path.split(dest)
    fno, ext = os.path.splitext(filename)
    batname = fno+'.bat'
    mydest = '"'+mypath+'"'
    f = open(batname, 'w')
    f.write(mydest)
    f.close()
    return batname

def RunLatexReplace(matchobj):
    linktext, dest = BreakLink(matchobj)
    batname = MakeBat(dest)
    return '\\href{run:%s}{\\color{darkgray}%s}'%(batname, linktext)


def FindAllinList(listin, entry):
    myarray=array(listin)
    indarray = where(myarray==entry)[0]
    return indarray.tolist()


def forwardlink(imagepath='forward_arrow.png',alttext='>', height=20):
    styletag='border: 0px solid;'
    styletag+='margin-bottom: -7px;'
    #styletag+='height: %spx;'%height
    return '<IMG alt="%s" src="%s" style="%s">'%(alttext, imagepath, styletag)

def backwardlink(imagepath='backward_arrow.png',alttext='<', height=20):
    return forwardlink(imagepath=imagepath, alttext=alttext, height=height)


def HTMLIMageString(imagepath, alttext=None, stylestr=''):
    if not alttext:
        alttext=imagepath
    styletag = 'border: 0px solid;'
    if stylestr:
        styletag+=stylestr
    return '<IMG alt="%s" src="%s" style="%s">'%(alttext, imagepath, styletag)


class Line:
    def __init__(self, stringin, reveallevel=None):
        self.string = rwkmisc.rwkstr(stringin)
        self.reveal = reveallevel
        self.CleanItems()


    def __repr__(self):
        return self.string


    def CleanItems(self, bullet='*'):
        self.string = self.string.strip()
        if self.string:
            while self.string[0] == bullet:
                self.string = self.string[1:]
        self.string = rwkmisc.rwkstr(self.string.strip())


    def LinkToLatex(self):
        p = re.compile('link{(.*?)}')
        #q = p.search(self.string)
        self.string = p.sub(LinkLatexReplace, self.string)


    def RunLinkToLatex(self):
        p = re.compile('rlink{(.*?)}')
        #q = p.search(self.string)
        self.string = p.sub(RunLinkLatexReplace, self.string)


    def LinkToHTML(self):
        p = re.compile('link{(.*?)}')
        #q = p.search(self.string)
        self.string = p.sub(LinkHTMLReplace, self.string)


    def RunToLatexBat(self):
        p = re.compile('run{(.*?)}')
        self.string = p.sub(RunLatexReplace, self.string)


    def RunToHTML(self):
        p = re.compile('run{(.*?)}')
        self.string = p.sub(RunHTMLReplace, self.string)


    def FigtoLatex(self):
        p = re.compile('fig{(.*?)}')
        self.string = p.sub(LatexFigReplace, self.string)


    def EqnToLatex(self):
        p = re.compile('eqn{(.*)}')
        self.string = p.sub(LatexEqnReplace, self.string)


    def EqnsToLatex(self):
        p = re.compile('eqns{(.*)}')
        self.string = p.sub(LatexEqnsReplace, self.string)


    def FigtoHTML(self):
        p = re.compile('fig{(.*?)}')
        self.string = p.sub(HTMLFigReplace, self.string)


    def PathToLatex(self):
        p = re.compile('path{(.*?)}')
        self.string = p.sub(pathReplace, self.string)


    def ToLatex(self, reveal=True, revealfirst=True):
        strout = ''
        self.RunLinkToLatex()
        self.LinkToLatex()
        self.RunToLatexBat()
        self.FigtoLatex()
        self.EqnToLatex()
        self.EqnsToLatex()
        self.PathToLatex()
        if self.reveal and reveal:
            if self.reveal!=-1 and (self.reveal!=1 or revealfirst):
                strout += '\onslide<'+str(self.reveal)+'->'
        strout += self.string
        return [strout]

    def ToHTML(self, reveal=True):
        self.LinkToHTML()
        self.FigtoHTML()
        self.RunToHTML()
        return [self.string]


class SectionHeading:
    def __init__(self, strin, linenum, secpat='^(s*): '):
        self.star = False
        self.rawstr = strin
        self.linenum = linenum
        q = re.search(secpat, strin)
        smatch = q.group(1)
        if '*' in smatch:
            smatch = smatch[0:-1]
            self.star = True
        self.secstr = 'sub'*(len(smatch)-1)+'section'
        junk, title = strin.split(':',1)
        self.title = title.strip()


    def ToLatex(self, reveal=True):
        startstr = '\\'+self.secstr
        if self.star:
            startstr += '*'
        return [startstr+'{'+self.title+'}']


class Figure:
    def __init__(self, path, width, units='percent', center=True):
        self.path = path
        self.width = width
        self.units = units
        self.center = center


    def ToLatex(self):
        print("not implemented yet.")


class Slide(txt_mixin.txt_list):
    def __init__(self, listin=[], filname=None, linenum=None):
        self.objlist = []
        self.verb = False
        self.fragile = False
        self.reveal = True
        self.rawlist = listin
        self.filname = filname
        self.linenum = linenum
        if listin:
            self.Parse()


    def drop_blanks_at_end(self):
        while not self.rawlist[-1]:
            self.rawlist.pop()


    def Parse(self):
        self.drop_blanks_at_end()
        self.StripList()
        self.GetTitle()
        self.ParseItemize()


    def StripList(self):
        self.list = [item.strip() for item in self.rawlist]
        ind = 0
        #get rid of leading blank lines
        while not self.list[ind]:
            self.list.pop(0)
        #get rid of trailng blank lines
        ind = len(self.list)-1
        while not self.list[ind]:
            self.list.pop()
            ind = len(self.list)-1


    def FindNestLevels(self, pat='^([\*#])*'):
        levels = []
        p=re.compile(pat)
        for item in self.list:
            q = p.match(item)
            if not q:
                curlevel = 0
            else:
                match = q.group()
                match = match.strip()
                curlevel = len(match)
                if curlevel > 0:
                    curlevel -= 1#subtract one because '* Title' is
                                 #the slide title and '** item' would
                                 #be the first itemized entry
            levels.append(curlevel)
        self.levels = levels


    def ParseItemize(self, debug=0):
        #Pdb().set_trace()
        self.FindNestLevels()
        self.objlist = []
        zeroinds = FindAllinList(self.levels, 0)
        if debug:
            print('self.levels = '+str(self.levels))
            print('zeroinds = '+str(zeroinds))
        self.revealinds = []
        #range(1,len(self.list)+1)
        p = re.compile('^\\s*\\\\vspace{.*?}')
        curreveal = 1
        for item in self.list:
            curout = curreveal
            #if type(item)==type(Line('')):
            q = p.search(item)
            if q:
                curout = -1
            self.revealinds.append(curout)
            if curout != -1:
                curreveal += 1
        prevind = -1
        if not zeroinds:
            mylist = ItemizedList(self.list)
            self.objlist.append(mylist)
            if debug:
                print('mylist = '+str(mylist))
        else:
            for ind in zeroinds:
                if ind != prevind and ind != (prevind+1):
                    self.objlist.append(ItemizedList(self.list[prevind+1:ind], reveallevel=self.revealinds[prevind+1]))
                self.objlist.append(Line(self.list[ind], reveallevel=self.revealinds[ind]))
                prevind = ind
            if prevind != (len(self.list)-1):
                self.objlist.append(ItemizedList(self.list[prevind+1:]))
        if debug:
            print('self.objlist = '+str(self.objlist))




    def GetTitle(self):
        firstline = self.list.pop(0)
        assert firstline[0:2]=='* ', 'Slide list did not start with "* Title"'
        self.title = firstline[2:].strip()
        p = re.compile('^([vfn]+:)(.*)')
        q = p.search(self.title)
        if q:
            first = q.group(1)
            last = q.group(2)
            if 'v' in first:
                self.verb = True
            if 'f' in first:
                self.fragile = True
            if 'n' in first:
                self.reveal = False
            self.title = last.strip()


    def ToLatex(self):#, reveal=None):
        reveal = self.reveal
        part1 = '\\begin{frame}%[label=current]'
        if self.fragile:
            part1 = '\\begin{frame}[fragile]%,label=current]'
        outlist = [part1,'\\frametitle{%s}'%self.title]
        if self.verb:
            #Pdb().set_trace()
            #list2 = [item.string for item in self.objlist]
            list2 = [item for item in self.rawlist[1:]]#the first element in rawlist must be the title
            outlist += list2
        else:
            for item in self.objlist:
                outlist.extend(item.ToLatex(reveal=reveal))
        outlist.append('\\end{frame}')
        return outlist


    def ToHTML(self, startnum, title, basename='slide',fmt='%0.3d',reveal=True, presdir=None, author='Ryan Krauss'):
        outlist = []
        out = outlist.append
        out('<div id="container">')
        out('<div id="top">')
        out('<h1>%s</h1>'%self.title)
        out('</div>')
        #out('<div id="slidebody">')
        out('<div id="leftnav">')
        out('<p>')
        out('')
        out('(outline goes here)')
        firstlink = CreateHTMLLink('slide001.html', 'start')
        out(firstlink)
        out('</p>')
        out('</div>')
        out('<div id="content">')
        #out('<h2>Subheading</h2>')
        for item in self.objlist:
            outlist.extend(item.ToHTML(reveal=reveal))
        out('</div>')
        out('<div id="footer">')
        out('<TABLE width=100%>')
        out('<TR>')
        out('<TD width=25% align=left>')
        out(author)
        out('</TD>')
        out('<TD width=50% align=center>')
        out(title)
        out('</TD>')
        navstr = ''
        if startnum > 1:
            prevname = CreateSlideName(startnum-1, basename=basename, fmt=fmt)
            prevlink = CreateHTMLLink(prevname,backwardlink())
            navstr += prevlink +' '
        nextname = CreateSlideName(startnum+1, basename=basename, fmt=fmt)
        nextlink = CreateHTMLLink(nextname,forwardlink())
        navstr += nextlink
        out('<TD width=25% align=right>')
        out(navstr)
        out('</TD>')
        out('</TR>')
        out('</TABLE>')
        out('</div>')
        out('</div>')
        mypath = basename+fmt%startnum+'.html'
        if presdir:
            mypath = os.path.join(presdir, mypath)
        #myhtml = textfiles.htmllist.htmllist([], mypath)
        myhtml = txt_mixin.txt_file_with_list([], mypath)
        headerlines = ['<style type="text/css">','body {background-color: black}','</style>']
        myhtml.insertheader(self.title, headerlines=headerlines)
        myhtml.extend(outlist)
        myhtml.append('</BODY>')
        myhtml.append('</HTML>')
        myhtml.tofile()
        return startnum+1




class ItemizedList(Slide):
    def __init__(self, listin=[], reveallevel=None):
        self.objlist = []
        self.rawlist = listin
        self.reveal = reveallevel
        if listin:
            self.Parse()

    def __repr__(self):
        if not hasattr(self, 'objlist'):
            return '\n'.join(self.rawlist)
        else:
            return '\n'.join([item.__repr__() for item in self.objlist])

    def FindNestLevels(self, pat='^(\*)*'):
        Slide.FindNestLevels(self, pat=pat)
        self.minlevel = min(self.levels)
        self.levels = [item-self.minlevel for item in self.levels]


    def Parse(self):
        self.StripList()
        self.ParseItemize()


    def ToLatex(self, reveal=True):
        if not self.objlist:
            return []
        startstr = '\\begin{itemize}'
        if reveal:
            startstr += '[<+-| alert@+>]'
        outlist = [startstr]
        for item in self.objlist:
            if isinstance(item, Line):
                outlist.append('\\item '+item.ToLatex(reveal=False)[0])
            else:
                outlist.extend(item.ToLatex(reveal=reveal))
        outlist.append('\\end{itemize}')
        return outlist


## <div id="navcontainer">
## <ul id="navlist">
## <li id="inactive">Item one</li>
## <ul id="subnavlist">
## <li id="inactive">Subitem one</li>
## <li id="inactive">Subitem two</li>

## <li id="active">Subitem three</li>
## <ul>
## <li id="hidden">Subsubitem one</li>
## <li id="hidden">Subsubitem two</li>
## <li id="hidden">Subsubitem three</li>
## </ul>
## <li id="hidden">Subitem four
## </ul>

## </li>
## <li id="hidden">Item two
## <li id="hidden">Item three
## <li id="hidden">Item four</li>

## </ul>
## </div>

    def ToHTML(self, reveal=True):
        outlist = []#'<div id="slidebody">']
        out = outlist.append
        out('<ul id="navlist">')
        for item in self.objlist:
            if isinstance(item, Line):
                outlist.append('<li id="inactive"> '+item.ToHTML(reveal=reveal)[0]+'</li>')
            else:
                outlist.extend(item.ToHTML(reveal=reveal))
        outlist.append('</ul>')
        return outlist



def NestedListToSlides(nestedlist, linenums=None):
    slidelist = []
    if linenums is None:
        linenums=[None]*len(nestedlist)
    for item, linenum in zip(nestedlist, linenums):
        curslide = Slide(listin=item, linenum=linenum)
        slidelist.append(curslide)
    return slidelist


class Outline(txt_mixin.txt_list):
    def Read(self, filename=None):
        if filename is None:
            filename = self.filename
        self.readfile(filename)
        self.rawlist = copy.copy(self.list)
        #self.list = [item.strip() for item in self.list]
        self.list = [item for item in self.list if item.find('%')!=0]#filter lines that start with %
        #self.rawlist = [item for item in self.rawlist if item.find('%')!=0]#filter lines that start with %
        self.DropOs()


    def DropOs(self):
        """To make it easy to use the same file for my outline and an
        inclass presentation, I need a way to have somethings in the
        outline that are omitted from the presentation.  For now, I am
        signifying the things to be omitted by putting an o at the end
        for their * or # list."""
        opat = r'^\s*[*#]o '
        o = re.compile(opat)
        self.list = [item for item in self.list if not o.match(item)]
        #self.rawlist = [item for item in self.rawlist if not o.match(item)]
        return self.list


    def FindSections(self, secpat='^([s*]*): '):
        indlist = self.findallre(secpat)#, match=False)
        seclist = [SectionHeading(self[ind], ind, secpat=secpat) for ind in indlist]
        return seclist, indlist


    def BreakOutline(self, pat='^\s*[\*#] ', secpat='^([s*]*): '):
        indlist = self.findallre(pat, match=False)
        secinds = self.findallre(secpat, match=False)
        totallist = indlist+secinds
        totallist.sort()
        nestedlist = []
        prevind = totallist.pop(0)
        while prevind in secinds:
            prevind = totallist.pop(0)
        before = self.list[0:prevind]
        for ind in totallist:
            if prevind in indlist:
                chunk = self.list[prevind:ind]
                if chunk:
                    nestedlist.append(chunk)
            prevind = ind
        last = self.list[prevind:]
        if last:
            nestedlist.append(last)
        return nestedlist, indlist


class Presentation(txt_mixin.txt_list):
    def __init__(self,listin=[],filename="",log=None, presdir=None):
        txt_mixin.txt_list.__init__(self,listin=listin,filename=filename,log=log)
        if presdir is None:
            presdir = os.getcwd()
        self.presdir = presdir


    def GetTexName(self):
        fno, ext = os.path.splitext(self.filename)
        if ext == ".pyp":
            self.pypname = self.filename
            self.texname = fno+'.tex'
        elif ext == '.tex':
            self.texname = self.filename
            self.pypname = ''
        return self.texname


    def Initialize(self):
        call_read = False
        filename = self.filename
        print('filename='+filename)
        if filename:
            fno, ext = os.path.splitext(filename)
            if ext == ".pyp":
                self.pypname = filename
                fno, ext = os.path.splitext(filename)
                self.texname = fno+'.tex'
                call_read = True
                outlinepath = filename
                filename = fno+".tex"
                print('outlinepath='+outlinepath)
                print('    exists='+str(os.path.exists(outlinepath)))

        if filename:
            folder, myname = os.path.split(filename)
            self.presdir = folder
        else:
            self.presdir = ''
        if call_read and os.path.exists(outlinepath):
            self.ReadOutline(outlinepath)
            self.ParseOutline()


    def ReadOutline(self, outlinefile):
        self.outline = Outline(filename=outlinefile)
        self.outline.Read()


    def ParseOutline(self):
        nestedlist, frameinds = self.outline.BreakOutline()
        self.sectionheadings, secinds = self.outline.FindSections()
        self.slides = NestedListToSlides(nestedlist, frameinds)

        mydict = dict(zip(frameinds, self.slides))
        dict2 = dict(zip(secinds, self.sectionheadings))
        mydict.update(dict2)
        self.dict = mydict



    def ToLatex(self, title='My Title', author='Ryan Krauss', theme='siue_white_nosubs', date='\\today', institute='Southern Illinois University Edwardsville', headerpath=None, headerinserts=[]):
        if headerpath is None:
            headerpath = texfilemixin.FindHeader(os.getcwd(), fn='beamerheader.tex')
            #headerpath = rwkos.FindFullPath('beamerheader.tex')#FindinPath
            print('headerpath='+headerpath)
        if not headerpath:
            print('could not find beamerheader.tex, exiting')
            return
        header = textfiles.rwkreadfile(headerpath)
        out = header.append
        mydict = {'title':title,'author':author,'date':date,'institute':institute,'usetheme':theme}
        for key, val, in mydict.iteritems():
            curpat = '\\'+key
            if not textfiles.searchlist(header, curpat):
                out(curpat+'{%s}'%val)
#        out('\\author{%s}'%author)
#        out('\\date{%s}'%date)
#        out('\\institute{%s}'%institute)
#        out('\\usetheme{%s}'%theme)
        if headerinserts:
            header.extend(headerinserts)
        bd = '\\begin{document}'
        if not textfiles.searchlist(header, bd):
            out(bd)
            out('')
        body = []
        myinds = self.dict.keys()
        myinds.sort()
        for ind in myinds:
            item = self.dict[ind]
            body.extend(item.ToLatex())
            body.append('')
            body.append('')
        body.append('\\end{document}')
        latexlines = header+body
        self.latexlist = txt_mixin.txt_list(latexlines, self.GetTexName())
        self.latexlist.tofile()
        return header+body


    def RunLatex(self, dvi=True):
        if not hasattr(self, 'latexlist'):
            self.ToLatex()
        return RunLatex(self.GetTexName(), dvi=dvi)
        #textfiles.latexlist.RunLatex(self.filename, dvi=dvi)


    def CopyHTMLFiles(self, sourcedir='pythonutil/html_pres_files/'):
        sourcedir = rwkos.FindFullPath(sourcedir)
        pat = os.path.join(sourcedir,'*')
        mylist = glob.glob(pat)
        destdir = self.presdir
        for item in mylist:
            folder, filename = os.path.split(item)
            destpath = os.path.join(destdir, filename)
            if not os.path.exists(destpath):
                shutil.copy2(item, destdir)


    def ToHTML(self, title, reveal=True, presdir=None, basename='slide'):
        if presdir is None:
            presdir = self.presdir
        if presdir and (not os.path.exists(presdir)):
            os.mkdir(presdir)
        slidenum = 1
        for item in self.slides:
            slidenum = item.ToHTML(slidenum, title, reveal=reveal, presdir=presdir, basename=basename)
        self.CopyHTMLFiles()

#############################################
#
#  Todo:
#
#     1. reveals with mixed in text don't quite work.  Follow the
#     example of overly_by_hand.tex.  ItemizedList needs to take
#     advantage of reveallevel for that to work.  Each item needs a
#     <#| alert@#>.  This feature should turn on only if a slide
#     contains Line's.
#
#     2. Figures aren't OO
#
#     3. Two column layouts?
#
#############################################

def PaperToPres(pathin, pathout, figstr='height:0.75'):
    """Open an existing LaTeX document and convert it to a skeleton
    pyp outline.  pathin is the path to the .tex file, presumably a
    conference paper or something.  pathout is the path to the .pyp
    file that will be the output.

    This function searches for all occurances of the following
    environments: eqnarray, equation, figure, lstlisting, and makes a
    slide of each."""
    latexlist = txt_mixin.txt_list([],'temp.tex')
    latexlist.readfile(pathin)
    latexlist.ReplaceInputs()

    #figures
    b4lines, envlines, afterlines, binds = latexlist.findenvironments('figure',getinds=True)
    figlist = [textfiles.latexlist.Figure(lines, ind) for lines, ind in zip(envlines, binds)]
    b4lines, eqnlines, afterlines, eqninds = latexlist.findenvironments('equation',getinds=True)
    eqnlist = [textfiles.latexlist.Equation(lines, ind) for lines, ind in zip(eqnlines, eqninds)]

    mydict = dict(zip(binds, figlist))
    eqndict = dict(zip(eqninds, eqnlist))
    mydict.update(eqndict)


    inds = mydict.keys()
    inds.sort()

    listout = []
    mycounter = textfiles.latexlist.Counter()

    for ind in inds:
        curitem = mydict[ind]
        curlines, mycoutner = curitem.ToPresentationList(mycounter, figstr=figstr)
        listout.extend(curlines)
        listout.append('')

    outlist = txt_mixin.txt_list(listout, pathout)
    outlist.tofile()
    return listout



if __name__=='__main__':
    curdir = os.getcwd()
    #mydir = r'E:\siue\classes\mechatronics\2007\intro'
    #mydir = 'siue/Research/papers/IMECE2007'
    mydir = '/home/ryan/mechatronics_2008/python_intro'
    mydir = rwkos.FindFullPath(mydir)
    os.chdir(mydir)

    #outlinefile = 'what_is_mechatronics.pyp'
    #outlinefile = 'presentation.pyp'
    #outlinefile = 'debug.pyp'
    outlinefile = 'python_intro.pyp'
    fno, ext = os.path.splitext(outlinefile)
    outname = fno +'_out.tex'
    outlinepath = os.path.join(mydir, outlinefile)
    outpath = os.path.join(mydir, outname)
    htmlout = 0
    mypres = Presentation(filename=outpath)
    mypres.ReadOutline(outlinepath)
    mypres.ParseOutline()
    mytitle='Introduction to Python'
    if htmlout:
        mypres.ToHTML(mytitle, reveal=False)
    else:
        latexlines = mypres.ToLatex(mytitle)
        mylatex = txt_mixin.txt_list(latexlines, outpath)
        mylatex.tofile()



    os.chdir(curdir)
