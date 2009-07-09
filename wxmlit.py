"""This module seeks to make an easy way to create wxmaxima wxm files
by creating a means for literate programming language."""


from pytex import readfile, writefile

import re, os, shutil, copy

from  IPython.Debugger import Pdb


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


def CtoPythonComments(matchobj):
    """To be used in a re.sub substitution.  Change '/* comment */' to
    '# comment'"""
    body = matchobj.group(1)
    return '#'+body.strip()


def ChangeCommentsToPython(listin):
    listout = []
    p = re.compile('/\*(.*)\*/')
    for item in listin:
        lineout = p.sub(CtoPythonComments, item)
        listout.append(lineout)
    return listout


class wxmFile:
    def __init__(self, pathin=None, comsym='#'):
        self.pathin = pathin
        self.comsym = comsym
        self.rawlist = []
        if pathin is not None:
            self.ReadFile()


    def ReadFile(self, path2=None):
        if not path2:
            path2 = self.pathin
        self.rawlist = readfile(path2)
        self.rawlist = CleanList(self.rawlist)


    def CreatePathout(self, ext):
        fno, junk = os.path.splitext(self.pathin)
        if ext[0] != '.':
            ext = '.'+ext
        pathout = fno+ext
        if os.path.exists(pathout):
            shutil.copy(pathout, fno+'_backup'+ext)
        return pathout
        
        
    def ToWLT(self, pathout=None):
        if pathout is None:
            pathout = self.CreatePathout('.wlt')
        listout = []
        out = listout.append
        list1 = self.rawlist[1:-2]#assuming .wxm files start with this line:
        #/* [wxMaxima batch file version 1] [ DO NOT EDIT BY HAND! ]*/
        #
        # and end with
        #
        #/* Maxima can't load/batch files which end with a comment! */
        #"Created with wxMaxima"$
        #
        # so that the first and last two lines need to be cut
        filt1 = '/* [wxMaxima: input   start ] */'
        filt2 = '/* [wxMaxima: input   end   ] */'
        filtlist = [filt1, filt2]
        filteredlines = [item for item in list1 if item not in filtlist]
        cleanlines = CleanList(filteredlines)
        self.cleanlines = cleanlines
        self.outlines = ChangeCommentsToPython(self.cleanlines)
        writefile(pathout, self.outlines)
        myout = wxmLitFile()
        myout.rawlist = copy.copy(self.outlines)
        myout.pathin = pathout
        return myout
    
    
class wxmLitFile(wxmFile):
##         /* [wxMaxima batch file version 1] [ DO NOT EDIT BY HAND! ]*/

##         /* [wxMaxima: input   start ] */
##         eq1:x+y=5;
##         /* [wxMaxima: input   end   ] */

##         /* [wxMaxima: input   start ] */
##         eq2:x-y=7;
##         /* [wxMaxima: input   end   ] */

##         /* [wxMaxima: input   start ] */
##         solve([eq1,eq2],[x,y]);
##         /* [wxMaxima: input   end   ] */

##         /* Maxima can't load/batch files which end with a comment! */
##         "Created with wxMaxima"$

    def ToWLT(self, pathout=None):
        raise "ThisIsGoingTheWrongWay", "This is probably not safe and has been disabled."
    

    def ToWXM(self, pathout=None):
        ############################
        #
        #  note that multi-line trailing comments are not handled correctly
        #
        ############################
        if pathout is None:
            pathout = self.CreatePathout('.wxm')
        listout = []
        out = listout.append
        out('/* [wxMaxima batch file version 1] [ DO NOT EDIT BY HAND! ]*/')
        eqstart = '/* [wxMaxima: input   start ] */'
        eqend = '/* [wxMaxima: input   end   ] */'

        eqopen = False#flag to tell whether or not there is an equation environment open
        prevline = None
        haseq = False#flag to tell if the equation environment already has an equation

        com_re = re.compile('^\\s*'+self.comsym+'(.*)')

        N = len(self.rawlist)-1

        for n, curline in enumerate(self.rawlist):
#            print('curline='+curline)
#            print('eqopen='+str(eqopen))
#            print('haseq='+str(haseq))
            if not curline and eqopen:
                out(eqend)
                out('')
                eqopen = False
                haseq = False
            if curline and not eqopen:
                eqopen = True
                out(eqstart)
            q = com_re.search(curline)
            if q:
                if eqopen and haseq and n!=N and self.rawlist[n+1]:
                    out(eqend)
                    out('')
                    out(eqstart)
                    eqopen = True
                    haseq = False
                out('/* '+q.group(1)+' */')
                if n==N or not self.rawlist[n+1]:
                    out(eqend)
                    out('')
                    eqopen = False
                    haseq = False
            elif curline:
                #the line is not a comment
                if haseq:
                    #close the current and start a new one
                    out(eqend)
                    out('')
                    out(eqstart)
                if curline[-1]!=';':
                    curline+=';'
                out(curline)
                haseq = True
        if eqopen:
            out(eqend)
            out('')
        out("/* Maxima can't load/batch files which end with a comment! */")
        out('"Created with Python"$')
        self.wxmlist = listout
        writefile(pathout, listout)
        myout = wxmFile()
        myout.rawlist = copy.copy(self.wxmlist)
        myout.pathin = pathout
        return myout
                
