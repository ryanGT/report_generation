import os, copy, re, shutil
import pytexutils, txt_mixin, pyp_parser
#reload(pyp_parser)

from IPython.core.debugger import Pdb
import pdb

import env_popper

ws = ' '*4

class Beamer_Figure(object):
    def __init__(self, pyp_figure):
        self.pyp_figure = pyp_figure
        mymap = ['caption','path','center','height','width']
        for item in mymap:
            cur_prop = getattr(self.pyp_figure, item)
            setattr(self, item, cur_prop)
        self.pne, self.ext = os.path.splitext(self.path)


    def to_latex(self):
        outlist = []
        if self.center:
            outlist.append('\\begin{center}')
        optstr = ''
        if self.width:
            optstr += 'width='+self.width
        if self.height:
            if optstr:
                optstr += ','
            optstr += 'height='+self.height
        main_str = '\\includegraphics'
        if optstr:
            main_str += '['+optstr+']'
        main_str += '{'+self.pne+'}'
        outlist.append(main_str)
        if self.center:
            outlist.append('\\end{center}')
        return outlist


class Two_Cols(object):
    def __init__(self, twocols_popper):
        self.popper = twocols_popper
        self.cols = [column(item) for item in self.popper.cols]


    def to_latex(self, width='0.45\\textwidth'):
        outlist = ['\\begin{columns}']
        for col in self.cols:
            outlist.append('\column{%s}' % width)
            outlist.extend(col.to_latex())
        outlist.append('\\end{columns}')
        return outlist



class Floating_Figure(object):
    def __init__(self, pyp_figure):
        self.pyp_figure = pyp_figure
        mymap = ['caption','path','center','height','width','label','placestr']
        for item in mymap:
            if hasattr(self.pyp_figure, item):
                cur_prop = getattr(self.pyp_figure, item)
            else:
                cur_prop = None
            setattr(self, item, cur_prop)
        self.pne, self.ext = os.path.splitext(self.path)


    def to_latex(self):
        outlist = []
        line1 = '\\begin{figure}'
        if self.placestr:
            line1 += self.placestr
        outlist.append(line1)
        if self.center:
            outlist.append('\\begin{center}')
        optstr = ''
        if self.width:
            optstr += 'width='+self.width
        if self.height:
            if optstr:
                optstr += ','
            optstr += 'height='+self.height
        main_str = '\\includegraphics'
        if optstr:
            main_str += '['+optstr+']'
        main_str += '{'+self.pne+'}'
        outlist.append(main_str)
        if self.center:
            outlist.append('\\end{center}')
        if self.caption:
            outlist.append('\\caption{'+self.caption+'}')
        if self.label:
            outlist.append('\\label{'+self.label+'}')
        outlist.append('\\end{figure}')
        return outlist



class Code_Chunk(object):
    def __init__(self, pyp_code):
        self.pyp_code = pyp_code
        mymap = ['lines']
        self.rawlines = [item.rawline for item in self.pyp_code.objlist]
        for item in mymap:
            if hasattr(self.pyp_code, item):
                cur_prop = getattr(self.pyp_code, item)
            else:
                cur_prop = None
            setattr(self, item, cur_prop)
        while not self.lines[0]:
            self.lines.pop(0)
        while not self.lines[-1]:
            self.lines.pop()


    def to_latex(self):
        outlist = ['\\begin{lstlisting}{}']
        #for line in self.rawlines:
        for line in self.lines:
            outlist.append(line)
        outlist.append('\\end{lstlisting}')
        return outlist


class Equation(object):
    def __init__(self, pyp_eqn):
        self.pyp_eqn = pyp_eqn
        self.env = pyp_eqn.env
        mymap = ['eqn']
        for item in mymap:
            if hasattr(self.pyp_eqn, item):
                cur_prop = getattr(self.pyp_eqn, item)
            else:
                cur_prop = None
            setattr(self, item, cur_prop)


    def to_latex(self):
        outlist = ['\\begin{%s}' % self.env]
        outlist.append(self.eqn)
        outlist.append('\\end{%s}' % self.env)
        return outlist


class Link(object):
    def __init__(self, pyp_link, env='equation'):
        self.pyp_link = pyp_link
        self.env = env
        mymap = ['link']
        for item in mymap:
            if hasattr(self.pyp_link, item):
                cur_prop = getattr(self.pyp_link, item)
            else:
                cur_prop = None
            setattr(self, item, cur_prop)


    def to_latex(self):
        outlist = [re.sub('link{(.*?)}', '\\href{\\1}{\\1}', \
                          self.pyp_link.rawline)]
        return outlist


Beamer_slide_mapper = {env_popper.pyp_figure:Beamer_Figure, \
                       env_popper.twocols:Two_Cols}

Document_mapper = {env_popper.pyp_figure:Floating_Figure, \
                   env_popper.pyp_code:Code_Chunk, \
                   env_popper.pyp_eqn:Equation, \
                   env_popper.pyp_link:Link}


class column(object):
    def __init__(self, col_in, baselevel=1, \
                 reveal=1):
        startstr = '\\begin{itemize}'
        if reveal:
            startstr += '[<+-| alert@+>]'
        self.startstr = startstr
        self.baselevel = baselevel
        self.col_in = col_in
        self.objlist = col_in.objlist

    def to_latex(self):
        mylist = pytexutils.objlist_to_latex(self.objlist, \
                                             Beamer_slide_mapper, \
                                             baselevel=self.baselevel, \
                                             startstr=self.startstr)
        return mylist


def _section_to_latex(section):
    outlist = []
    if hasattr(section, 'title'):
        if section.title:
            sec_str = '\\'+'sub'*section.sublevel+'section'
            if hasattr(section, 'starred'):
                if section.starred:
                    sec_str += '*'
            sec_str += '{'+section.title.strip()+'}'
            outlist.append(sec_str)
    if hasattr(section, 'body'):
        if section.body:
            body_lines = [item.rawline for item in section.body]#<-- this is bad
            outlist.extend(body_lines)
    return outlist


def lines_to_latex(linelist, baselevel=0, startstr='\\begin{itemize}'):
    """Convert a list of pyp_parser.lines into latex code, accounting
    for the possiblity that the lines may contain nested lists
    (itemize)."""
    line_parser = env_popper.pyp_env_popper(linelist, def_level=0)
    line_parser.Execute()
    outlist = pytexutils.objlist_to_latex(line_parser.objlist, \
                               Document_mapper,
                               baselevel=baselevel, \
                               startstr=startstr)
    return outlist


def section_to_document(section):
    outlist = _section_to_latex(section)
    if section.has_subs:
        for cur_sub in section.subsections:
            outlist.extend(section_to_document(cur_sub))
    else:
        body_list = lines_to_latex(section.lines)
        outlist.extend(body_list)
    return outlist


def section_to_Beamer(section):
    outlist = _section_to_latex(section)
    if hasattr(section, 'slides'):
        for cur_slide in section.slides:
            my_slide = slide(cur_slide)
            outlist.extend(my_slide.to_latex())
    if section.has_subs:
        for cur_sub in section.subsections:
            outlist.extend(section_to_Beamer(cur_sub))
    return outlist


def list_or_str(line):
    """Allow input of either a string or a list when a list is really
    expected.  Strings are put inside a list, becoming a one item
    list.  All other inputs are simply passed."""
    if type(line) == str:
        return [line]
    return line


class pyp_to_other(txt_mixin.txt_file_with_list):
    def __init__(self, pathin, parser_class=pyp_parser.pyp_file):
        self.path = pathin
        self.parser = parser_class(pathin)
        self.parser.parse()


    def to_latex(self, myfunc=section_to_document, sections=None):
        outlist = []
        if sections:
            mysections = self.get_sections(sections)
        else:
            mysections = self.parser.sections
        for cur_section in mysections:
            cur_list = myfunc(cur_section)
            outlist.extend(cur_list)
        self.latex_list = outlist
        return outlist


    def get_sections(self, seclist):
        """Return the sections of self.parser.sections that corrspond
        to the indices in seclist, which must be a list of integers."""
        if type(seclist) == int:
            seclist = [seclist]
        outsections = [self.parser.sections[ind]  for ind in seclist]
        return outsections




vf_pat = '([vf]+):(.*)'
vf_re = re.compile(vf_pat)




class slide(object):
    def parse_title(self):
        self.verb = False
        self.fragile = False
        self.reveal = True
        raw_title = self.raw_title.string
        q = vf_re.search(raw_title)
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
        else:
            self.title = raw_title.strip()
        return self.title


    def __init__(self, slidein):
        self.raw_title = slidein.title
        self.body_lines = slidein.body_lines
        self.objlist = slidein.body_parser.objlist
        self.slidein = slidein
        self.parse_title()


    def to_latex(self, baselevel=1):
        reveal = self.reveal
        part1 = '\\begin{frame}%[label=current]'
        if self.fragile:
            part1 = '\\begin{frame}[fragile]%,label=current]'

        startstr = '\\begin{itemize}'
        if reveal:
            startstr += '[<+-| alert@+>]'

        outlist = [part1,'\\frametitle{%s}'%self.title]
        if self.verb:
            list2 = [item.string for item in self.body_lines]
            outlist += list2
        else:
            mainlist = pytexutils.objlist_to_latex(self.objlist, \
                                        Beamer_slide_mapper, \
                                        baselevel=baselevel, \
                                        startstr=startstr)
            outlist.extend(mainlist)
##             prev_level = 1
##             for item in self.objlist:#body_lines:
##                 cur_ws = ws*(item.level-1)
##                 if item.level < prev_level and (prev_level > 1):
##                     prev_ws = ws*(prev_level-1)
##                     close_list = [prev_ws+'\\end{itemize}']*(prev_level-item.level)
##                     outlist.extend(close_list)
##                 if item.level <= 1:
##                     if Beamer_slide_mapper.has_key(type(item)):
##                         my_class = Beamer_slide_mapper[type(item)]
##                         my_instance = my_class(item)
##                         outlist.extend(my_instance.to_latex())
##                     else:
##                         outlist.append(item.string)
##                 if item.level > prev_level:
##                     outlist.append(cur_ws+startstr)
##                 if item.level >=2:
##                     outlist.append(cur_ws+'\\item '+item.string)
##                 prev_level = item.level

##             #close any open itemize's:
##             if prev_level != 0:
##                 num_to_close = prev_level-1
##                 for n in range(num_to_close):
##                     cur_ws = (num_to_close-n)*ws
##                     outlist.append(cur_ws+'\\end{itemize}')

        outlist.append('\\end{frame}')
        outlist.extend(['']*2)
        return outlist



class pyp_to_presentation(pyp_to_other):
    def __init__(self, pathin, parser_class=pyp_parser.pyp_presentation):
        pyp_to_other.__init__(self, pathin, parser_class=parser_class)



class pyp_to_Beamer(pyp_to_presentation):
    def to_latex(self, myfunc=section_to_Beamer, sections=None):
        return pyp_to_presentation.to_latex(self, myfunc=myfunc, sections=sections)


    def get_slide(self, index):
        return self.parser.get_slide(index)


class Latex_document(txt_mixin.txt_file_with_list):
    def __init__(self, pathin, converter_class=pyp_to_other, pathout=None):
        txt_mixin.txt_file_with_list.__init__(self, pathin=None)#temporarily override pathin so that the parent __init__ doesn't read in the file
        self.pathin = pathin
        if pathin:
            self.dir, self.name = os.path.split(pathin)
        else:
            self.dir = None
            self.name = None
        self.converter = converter_class(pathin)
        if pathout is not None:
            self.pathout = pathout
        else:
            path_no_ext, ext = os.path.splitext(pathin)
            self.pathout = path_no_ext+'.tex'


    def add_header(self, headername='header.tex',\
                   headerinserts=[]):
        header = []
        if self.dir:
            search_dir = self.dir
        else:
            search_dir = os.getcwd()
        headerpath = os.path.join(search_dir, headername)
        header_list = pytexutils.readfile(headerpath)
        header.extend(header_list)
        header.extend(headerinserts)
        bdstr = '\\begin{document}'
        if bdstr not in header:
            header.append(bdstr)
        self.header = txt_mixin.txt_list(header)


    def append_to_header(self, linelist):
        linelist = list_or_str(linelist)
        assert hasattr(self, 'header'), "You must call add_header before \n" + \
               "you can append to the header."
        lastline = self.header.pop()
        assert lastline == '\\begin{document}', "Expected the last line of the \n" + \
               "header to be \\begin{document}"
        self.header.extend(linelist)
        self.header.append(lastline)


    def conditional_header_append(self, pat, line=None):
        """Insert line into self.header if pat is not found in
        self.header."""
        if line is None:
            line = pat
        assert hasattr(self, 'header'), "You must call add_header before \n" + \
               "you can append to the header."
        if not self.header.findnext(pat):
            self.append_to_header(line)


    def require_package(self, packagename):
        self.conditional_header_append('\\usepackage{%s}' % packagename)


    def to_latex(self, sections=None, add_header=True, **kwargs):
        if not hasattr(self, 'header') and add_header:
            self.add_header(**kwargs)
        self.latex_body = txt_mixin.txt_list(self.converter.to_latex(sections=sections))


    def insert_at_beginning_of_body(self, lines):
        if type(lines) == str:
            lines = [lines]
        self.latex_body[0:0] = lines


    def save(self):
        if not hasattr(self, 'latex_body'):
            self.to_latex()
        self.fulllist = self.header+self.latex_body
        ed = '\\end{document}'
        if ed not in self.fulllist and hasattr(self,'header'):
            self.fulllist.append(ed)
        pytexutils.writefile(self.pathout, self.fulllist)


    def run_latex(self, dvi=0, openviewer=False, **kwargs):
        viewer_filename = pytexutils.RunLatex(self.pathout, dvi=dvi, \
                                              openviewer=openviewer, \
                                              **kwargs)
        self.viewer_filename = viewer_filename
        return self.viewer_filename

    def RunLatex(self, **kwargs):
        return self.run_latex(**kwargs)


class Beamer_pres(Latex_document):
    def __init__(self, pathin, draft=True, author='Ryan Krauss',\
                title='My Title', date='\\today',
                theme='siue_white_nosubs',
                institute='Southern Illinois University Edwardsville', \
                converter_class=pyp_to_Beamer):
        Latex_document.__init__(self, pathin, converter_class=converter_class)
        self.draft = draft
        self.author = author
        self.title = title
        self.date = date
        self.theme = theme
        self.institute = institute


    def get_slide(self, index):
        return self.converter.get_slide(index)


    def add_header(self, headername='beamerheader_v2.tex',\
                   headerinserts=[]):
        Latex_document.add_header(self, headername, headerinserts=headerinserts)
        header1 = ['\\documentclass[t,12pt,']
        if self.draft:
            header1.append('handout')
        header1.append(']{beamer}')

        self.header[0:0] = header1
        header2 = []
        out = header2.append
        header_items = ['date','author','title','theme','institute']
        header_dict = dict(zip(header_items, header_items))
        header_dict['theme']='usetheme'
        for item in header_items:
            cur_prop = getattr(self, item)
            if cur_prop:
                cur_pat = '\\'+header_dict[item]+'{%s}'
                out(cur_pat % cur_prop)
        self.header[-1:-1] = header2#Latex_document.add_header adds
                                    #the \begin{document} line.  This
                                    #code inserts header2 before that
                                    #line.


    def to_latex(self, sections=None, slidenums=None, **kwargs):
        if slidenums is None:
            Latex_document.to_latex(self, sections=sections, **kwargs)
        else:
            if type(slidenums) == int:
                slidenums = [slidenums]
            self.add_header(**kwargs)
            self.latex_body = []
            for ind in slidenums:
                cur_slide = slide(self.get_slide(ind))
                cur_latex = cur_slide.to_latex()
                self.latex_body.extend(cur_latex)
                self.latex_body.extend(['\n']*2)


if __name__ == '__main__':
    import rwkos
    #pres_paths = []
    pres_paths = ["/home/ryan/IMECE2008/pres_outline.pyp"]
             #'/home/ryan/siue/Research/applied_controls_group/inaugural_meeting/inaugural_meeting.pyp',\
             #'/home/ryan/pythonutil/pyp_tests/test1.pyp',\
             #'/home/ryan/pythonutil/pyp_tests/test2.pyp',\
             #    '/home/ryan/pythonutil/pyp_tests/test3.pyp',\
             #'/home/ryan/pythonutil/pyp_tests/debug1.pyp',\
             #'/home/ryan/pythonutil/pyp_tests/debug2.pyp'
    #         ]

    #doc_paths = ['/home/ryan/siue/Research/SRF_proposal_2008/outline.pyp']
    doc_paths = []

    test_list = []
    for item in pres_paths:
        cur_path = rwkos.FindFullPath(item)
        #my_pyp = pyp_to_Beamer(cur_path)
        #my_pyp.to_latex()
        draft = 0
        my_pres = Beamer_pres(cur_path, draft=draft,\
                              title='Applied Controls Research Group: Inaugural Meeting',\
                              theme='siue_Cambridge',)
        my_pres.to_latex(slidenums=-1)
        my_pres.save()
        #my_pres.run_latex()


    for item in doc_paths:
        cur_path = rwkos.FindFullPath(item)
        my_doc = Latex_document(cur_path)
        my_doc.to_latex()
        my_doc.save()
        my_doc.run_latex()
