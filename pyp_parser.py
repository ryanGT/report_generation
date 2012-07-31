import os, copy, re, shutil
import pytexutils, txt_mixin
#reload(txt_mixin)

#from IPython.core.debugger import Pdb
import pdb

import env_popper

#secpat = '^s\\**:(.*)'
secpat = '^s(\\*)*:(.*)'

from pyp_basics import line, section, tweak_section_linenums, \
     list_of_sections

bad_index_msg = "Slide index is greater than \n" + \
                "or equal to the total number of slides:\n" + \
                "index=%s, total=%s"

#############################
#
# How should parsing for fig and code and other blocks work?
#
# --> pass in a list of lines
# --> find fig, code and other environments
#      o handle multi-line blocks as neccessary
# --> return a list of line, figure, code, or other objects
#
# A latex writer would then take that list of parser objects
# and know how to convert them to latex (possibly creating
# latex objects based on the parser type first).
#
#     ? Am I really succeeding at separating parsing and outputing?
#
#     ? Is this accomplishing something?
#
#
#############################


class pyp_file(txt_mixin.txt_file_with_list):
    def __init__(self, pathin, section_class=section):
        txt_mixin.txt_file_with_list.__init__(self, pathin)
        self.section_class = section_class

    def _find_section_line_nums(self):
        templist = self.findallre(secpat)
        self.section_line_nums = tweak_section_linenums(templist)


    def find_sections(self):
        self.sections = []
        if not hasattr(self, 'section_line_nums'):
            self._find_section_line_nums()
        self.sections = list_of_sections(self.list, self.section_line_nums, \
                                         myclass=self.section_class)


    def parse(self):
        if not hasattr(self, 'sections'):
            self.find_sections()
        [sec.parse() for sec in self.sections]



class slide(object):
    """A class to represent a slide created from pyp text.  The title
    is assumed to be in the first line, which has one bullet."""
    def __init__(self, lines):
        self.rawlines = lines
        self.title = lines[0]
        self.body_lines = copy.copy(lines[1:])
        while not self.body_lines[-1].string:
            self.body_lines.pop()


    def parse(self):
        self.body_parser = env_popper.pyp_env_popper(self.body_lines)
        self.body_parser.Execute()



class slide_parser(object):
    """A class to convert a list of line objects into
    Beamer or s5 slides.  The text before the first slide title line
    will be placed in a body, the rest will be broken into a list of
    slides."""
    def __init__(self, lines):
        self.lines = lines


    def _get_title_inds(self, title_level=1):
        title_inds = []
        for n, item in enumerate(self.lines):
            if item.level == title_level:
                title_inds.append(n)
        title_inds.append(None)
        return title_inds


    def break_into_slides(self, title_level=1):
        self.title_inds = self._get_title_inds(title_level=title_level)
        prevind = self.title_inds[0]
        self.body = None
        if prevind != 0:
            self.body = self.lines[0:prevind]
        slide_list = []
        for ind in self.title_inds[1:]:
            cur_slide = slide(self.lines[prevind:ind])
            slide_list.append(cur_slide)
            prevind = ind
        self.slide_list = slide_list
        return slide_list


class section_with_slides(section):
    def __init__(self, listin, subclass=None, **kwargs):
        if subclass is None:
            subclass = section_with_slides
        section.__init__(self, listin, subclass=subclass, **kwargs)


    def parse_lines(self):
        """This only gets called on sections that don't have
        subsections, i.e. on the lowest level.  There should be only
        body and bullet pieces at this point."""
        section.parse_lines(self)
        self.slide_parser = slide_parser(self.lines)
        self.slides = self.slide_parser.break_into_slides()
        [slide.parse() for slide in self.slides]
        self.body = self.slide_parser.body


    def total_num_slides(self):
        n = 0
        if self.has_subs:
            for cur_sub in self.subsections:
                n += cur_sub.total_num_slides()
        else:
             n = len(self.slides)
        return n


    def _get_slide(self, index, start=0):
        nn = self.total_num_slides()
        if index >= nn+start:
            return None, start+nn
        else:
            if self.has_subs:
                for cur_sub in self.subsections:
                    slide, start = cur_sub._get_slide(index, start=start)
                    if slide:
                        return slide, start
            else:
                fn = index-start
                return self.slides[fn], fn


    def get_slide(self, index):
        n = self.total_num_slides()
        assert index < n, bad_index_msg % (index, n)
        start = 0
        if self.has_subs:
            for cur_sub in self.subsections:
                slide, start = cur_sub._get_slide(index, start)
                if slide:
                    return slide, start
        else:
            return self._get_slide(index, start)



class pyp_presentation(pyp_file):
    def __init__(self, pathin, section_class=section_with_slides):
        txt_mixin.txt_file_with_list.__init__(self, pathin)
        self.section_class = section_class


    def total_num_slides(self):
        n = 0
        for sections in self.sections:
                n += sections.total_num_slides()
        return n


    def get_slide(self, index):
        start = 0
        n = self.total_num_slides()
        assert index < n, bad_index_msg % (index, n)
        if index < 0:
            index = n + index
        #Pdb().set_trace()
        for section in self.sections:
            num_slides = section.total_num_slides()
            if start + num_slides <= index:
                start += num_slides
            else:
                ind = index-start
                slide, indout = section.get_slide(ind)
                return slide


if __name__ == '__main__':
    import rwkos
    paths = [#'/home/ryan/siue/Research/applied_controls_group/inaugural_meeting/inaugural_meeting.pyp',\
             #'/home/ryan/pythonutil/pyp_tests/test1.pyp',\
             #'/home/ryan/pythonutil/pyp_tests/test2.pyp',\
             #'/home/ryan/pythonutil/pyp_tests/test3.pyp'
             #'/home/ryan/siue/classes/482/lectures/week_05/proposal_questions.pyp'
             "/home/ryan/IMECE2008/pres_outline.pyp"
            ]

    test_list = []
    for item in paths:
        cur_path = rwkos.FindFullPath(item)
        my_pyp = pyp_presentation(cur_path)
        #my_pyp.find_sections()
        my_pyp.parse()
        test_list.append(my_pyp)
