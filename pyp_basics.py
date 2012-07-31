import os, copy, re, shutil
import pytexutils, txt_mixin
#reload(txt_mixin)

#from IPython.core.debugger import Pdb

#secpat = '^s\\**:(.*)'
secpat = '^s(\\*)*:(.*)'

linepat = '^\s*([\*#]+) (.*)'
line_re = re.compile(linepat)


def tweak_section_linenums(listin):
    if not listin:
        listin.append(0)
    elif listin[0] != 0:
        listin.insert(0,0)
    listin.append(None)
    return listin



class line(object):
    def __init__(self, linein):
        self.rawline = linein
        q = line_re.match(linein)
        if q:
            self.bullet = q.group(1)
            self.string = q.group(2)
            self.level = len(self.bullet)
        else:
            self.bullet = None
            self.string = linein
            self.level = 0


    def __repr__(self):
        mystr = 'pyp_parser.line object:string='+self.string+ \
                ', level=%s, bullet=%s'%(self.level, self.bullet)
        return mystr



class section(object):
    def __init__(self, listin, pat=secpat, subclass=None, sublevel=0):
        self.list = txt_mixin.txt_list(listin)
        self.pat = pat
        self.re_p = re.compile(self.pat)
        if subclass is None:
            subclass = section
        self.subclass = subclass
        self.sublevel = sublevel


    def get_title(self):
        self.title = None
        q = self.re_p.match(self.list[0])
        if q:
            line0 = self.list.pop(0)
            self.title = q.group(2)
            if q.group(1):
                self.starred = len(q.group(1))
            else:
                self.starred = 0
        return self.title


    def find_nest_levels(self, pat='^\s*([\*#]*)'):
        levels = []
        p = re.compile(pat)
        for item in self.list:
            q = p.match(item)
            if not q:
                curlevel = 0
            else:
                match = q.group(1)
                match = match.strip()
                curlevel = len(match)
            levels.append(curlevel)
        self.levels = levels



    def parse_lines(self):
        self.lines = [line(item) for item in self.list]
        self.levels = [item.level for item in self.lines]



    def parse(self):
        if not hasattr(self, 'title'):
            self.get_title()
        if self.pat[0] == '^':
            ind = 1
        else:
            ind = 0
        self.subpat = '^s'+self.pat[ind:]#this should insert one 's'
        self.sub_line_nums = self.list.findallre(self.subpat)
        self.subsections = []
        if not self.sub_line_nums:
            self.has_subs = False
            self.parse_lines()
        else:
            self.has_subs = True
            self.sub_line_nums = tweak_section_linenums(self.sub_line_nums)
            self.subsections = list_of_sections(self.list, self.sub_line_nums, \
                                                pat=self.subpat, myclass=self.subclass,\
                                                sublevel=self.sublevel+1)
            for subsec in self.subsections:
                subsec.parse()




def list_of_sections(listin, inds, myclass=section, sublevel=0, **kwargs):
    listout = []
    prevind = inds[0]
    for ind in inds[1:]:
        curlist = listin[prevind:ind]
        cur_section = myclass(curlist, sublevel=sublevel, **kwargs)
        listout.append(cur_section)
        prevind = ind
    return listout
