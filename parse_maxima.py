import txt_mixin, texfilemixin


def ParseMaximaOutput(linesin, frlist=[], removelist=['$$'], lhs='', combined=1, wrap=0, maxwidth=130, rhs=''):
    myeq = MaximaEquation(linesin)
    myeq.InitialCleaning(removelist=removelist, lhs=lhs, rhs=rhs)
    myeq.FixPmatrix()
    myeq.FixOver()
    myeq.ReplaceFRPatterns(frlist)
    if wrap:
        myeq.Wrap(maxwidth=maxwidth)
        return myeq.wrappedlines
    else:
        return [myeq.string]


class MaximaEquation(txt_mixin.txt_list, texfilemixin.TexFileMixin):
    """This class exists to read the Tex output of Maxima and turn it
    into LaTeX code that I like better, possibly replacing variable
    names with nice LaTeX symbols like th --> \theta.

    It also takes the multi-line Maxima Tex output and combines it
    into one line."""
    def __init__(self, listin=[], pathin=None):
        self.listin = listin
        self.string = ''
        if pathin:
            self.listin = rwkreadfile(pathin)


    def FullParse(self, frlist=[], removelist=['$$'], lhs='', rhs=''):
        self.InitialCleaning(removelist=removelist, lhs=lhs, rhs=rhs)
        self.FixOver()
        self.FixPmatrix()
        self.ReplaceFRPatterns(frlist=frlist)


    def CombinedLines(self, lines=[]):
        if not lines:
            lines = self.listin
        outstr=combinedlines(lines)
        self.string = outstr
        return self.string


    def InitialCleaning(self, removelist=['$$'], lhs='', rhs='', allowtwoequals=False):
        """Remove unwanted symbols from the Maxima output, insert a
        right or left hand side if needed and combined the list into
        one string if combined is True (return a one item list
        containing the string for consistancy).

        allowtwoequals=False means looks for an equals sign in
        self.listin and don't add self.lhs if you find one."""
        linesout=[]
        hasequals = searchlist(self.listin, '=')
        if (not hasequals) or  allowtwoequals:
            if lhs:
                if lhs.find('=')==-1:
                    lhs+='='
                linesout.append(lhs)
        for line in self.listin:
            curout=line
            for item in removelist:
                curout=curout.replace(item,' ')
            linesout.append(curout)
        if rhs:
            linesout.append('='+rhs)
        self.string = self.CombinedLines(linesout)
        return self.string


    def _GetReady(self):
        """Prepare for search and replace operations like FixPmatrix and FixOver"""
        if not self.string:
            self.InitialCleaning()


    def FixPmatrix(self):
        self._GetReady()
        self.string = FixPmatrix(self.string)


##     def FixPmatrix_pyparsing(self):
##         self._GetReady()
##         PMATRIX = Literal(r"\pmatrix")
##         nestedBraces = nestedExpr("{","}")
##         #nestedBraces.enablePackrat()
##         nestedBraces.setParseAction(keepOriginalText)
##         grammar = PMATRIX+nestedBraces
##         #grammar.enablePackrat()
##         grammar.setParseAction(pyparsingCleanPmatrix)
##         self.string = grammar.transformString(self.string)
                                          

    def FixOver(self):
        self._GetReady()
        self.string = FixOver(self.string)


    def ReplaceFRPatterns(self, frlist):
        strout = self.string
        for curtuple in frlist:
            fent = curtuple[0]
            rent = curtuple[1]
            if len(curtuple)>2:
                useb = curtuple[2]
            else:
                useb = 1
            if useb:
                strout=re.sub('\\b'+fent+'\\b',rent,strout)
            else:
                strout=re.sub(fent,rent,strout)
        self.string = strout


    def Wrap(self, maxwidth=130):
        wraplines=wraponeeqline(self.string, maxwidth)
        outlines=[]
        for line in wraplines:
            curout=nestparen(line)
            if len(curout)>maxwidth:
                outlines.extend(forcewrap(curout,maxwidth))
            else:
                outlines.append(curout)
        self.wrappedlines = outlines
        return self.wrappedlines

            

##     def ParseMaximaOutput_old_broken(self, frlist=[], removelist=['$$'], lhs='', combined=1, wrap=0, maxwidth=130,rhs=''):
##         linesout=[]
##         if wrap:
##             combined=1
##         if lhs:
##             if lhs.find('=')==-1:
##                 lhs+='='
##             linesout.append(lhs)
##         for line in self.listin:
##             curout=line
##             for item in removelist:
##                 curout=curout.replace(item,' ')
##             usemap=0
##             if usemap:
##                 for rule in replacerules(frlist):
##                     if lhs:
##                         lhs=rule(lhs)
##                     curout=rule(curout)
##             linesout.append(curout)
##         if rhs:
##             linesout.append('='+rhs)
##         if combined:
##             outstr=combinedlines(linesout)
##             outstr=FixOver(outstr)
##             outstr=FixPmatrix(outstr)
##             if wrap:
##                 wraplines=wraponeeqline(outstr,maxwidth)
##                 outlines=[]
##                 for line in wraplines:
##                     curout=nestparen(line)
##                     if len(curout)>maxwidth:
##                         outlines.extend(forcewrap(curout,maxwidth))
##                     else:
##                         outlines.append(curout)
##                 return outlines
##             else:
##                 outstr=nestparen(outstr)
##                 return [outstr]
##         else:
##             return linesout
