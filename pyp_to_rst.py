#!/usr/bin/env python
import os, copy, re, shutil
import pytexutils

from IPython.core.debugger import Pdb
import pdb

from pytexutils import break_at_pipes, OptionsDictFromList

from rst_creator import *
import txt_mixin

class list_regexp_replacer:
    """A class for running specialized regexp search and replace on
    each line of a list."""
    def __init__(self, pat, flags=0, match=False):
        self.pat = pat
        self.p = re.compile(self.pat, flags=flags)
        self.match = match


    def replace_list(self, listin):
        listout = []
        for line in listin:
            curlist = self.replace_line(line)
            if type(curlist) == list:
                listout.extend(curlist)
            else:
                listout.append(curlist)
        return listout


    def replace_line(self, linein):
        """Call self.p.search or match depending on the value of
        self.match.  These functions call the corresponding regexp
        functions.  Return linein unmodified if there is no match.
        Otherwise, return a string or list containing the desired
        replacement stuff.

        This function should be overridden by derived classes.  By
        default, it does nothing."""
        return linein


ws = ' '*2


class rst_list_level_1(rst_decorator):
    def __call__(self, stringin):
        return '- '+ stringin


class rst_list_level_2(rst_decorator):
    def __call__(self, stringin):
        return ws + '- ' + stringin


class rst_list_level_3(rst_decorator):
    def __call__(self, stringin):
        return ws*2 + '- ' + stringin


class section_to_level_1(list_regexp_replacer):
    def __init__(self, pat='^s:(.*)', **kwargs):
        list_regexp_replacer.__init__(self, pat=pat, **kwargs)
        self.decorator = rst_section_level_1()


    def replace_line(self, linein):
        q = self.p.search(linein)
        if q:
            section = q.group(1)
            return self.decorator(section)
        else:
            return linein


class section_to_section(list_regexp_replacer):
    def __init__(self, pat='^s\\**: *(.*)', **kwargs):
        list_regexp_replacer.__init__(self, pat=pat, **kwargs)
        self.decorator = rst_section_dec()


    def replace_line(self, linein):
        q = self.p.search(linein)
        if q:
            section = q.group(1)
            section = section.strip()
            return self.decorator(section)
        else:
            return linein

class subsection_to_subsection(section_to_section):
    def __init__(self, pat='^ss\\**: *(.*)', **kwargs):
        list_regexp_replacer.__init__(self, pat=pat, **kwargs)
        self.decorator = rst_subsection_dec()


class subsubsection_to_subsubsection(subsection_to_subsection):
    def __init__(self, pat='^sss\\**: *(.*)', **kwargs):
        list_regexp_replacer.__init__(self, pat=pat, **kwargs)
        self.decorator = rst_subsubsection_dec()


class figure_ref(list_regexp_replacer):
    def __init__(self, pat=r'([Ff]igure[ ~]\\ref{.*?})', **kwargs):
        list_regexp_replacer.__init__(self, pat=pat, **kwargs)


    def replace_line(self, linein):
        q = self.p.search(linein)
        if q:
            return self.p.sub('`\\1`', linein)
        else:
            return linein

class lstinline(figure_ref):
    def __init__(self, pat=r'(\\lstinline!.*?!)', **kwargs):
        list_regexp_replacer.__init__(self, pat=pat, **kwargs)

class inlineeq(figure_ref):
    def __init__(self, pat=r'(\$.*?\$)', **kwargs):
        list_regexp_replacer.__init__(self, pat=pat, **kwargs)

class one_asterisk_to_level_2(section_to_level_1):
    def __init__(self, pat='^\* (?:[vf:]*)(.*)', **kwargs):
        list_regexp_replacer.__init__(self, pat=pat, **kwargs)
        self.decorator = rst_section_level_2()


class two_asterisks_to_list_level_1(section_to_level_1):
    def __init__(self, pat='^\s*\*\* (.*)', **kwargs):
        list_regexp_replacer.__init__(self, pat=pat, **kwargs)
        self.decorator = rst_list_level_1()


class three_asterisks_to_list_level_2(section_to_level_1):
    def __init__(self, pat='^\s*\*\*\* (.*)', **kwargs):
        list_regexp_replacer.__init__(self, pat=pat, **kwargs)
        self.decorator = rst_list_level_2()


class four_asterisks_to_list_level_3(section_to_level_1):
    def __init__(self, pat='^\s*\*\*\*\* (.*)', **kwargs):
        list_regexp_replacer.__init__(self, pat=pat, **kwargs)
        self.decorator = rst_list_level_3()


class one_asterisks_to_list_level_1(section_to_level_1):
    def __init__(self, pat='^\s*\* (.*)', **kwargs):
        list_regexp_replacer.__init__(self, pat=pat, **kwargs)
        self.decorator = rst_list_level_1()


class two_asterisks_to_list_level_2(section_to_level_1):
    def __init__(self, pat='^\s*\*\* (.*)', **kwargs):
        list_regexp_replacer.__init__(self, pat=pat, **kwargs)
        self.decorator = rst_list_level_2()


class three_asterisks_to_list_level_3(section_to_level_1):
    def __init__(self, pat='^\s*\*\*\* (.*)', **kwargs):
        list_regexp_replacer.__init__(self, pat=pat, **kwargs)
        self.decorator = rst_list_level_3()


class pyp_to_rst(object):
    def __init__(self, pyppath):
        self.pyp_path = pyppath
        self.main_dir, self.pyp_name = os.path.split(self.pyp_path)
        self.pyp_list = txt_mixin.txt_list(pytexutils.readfile(pyppath))
        self.rst_list = copy.copy(self.pyp_list)
        path_no_ext, ext = os.path.splitext(pyppath)
        self.rst_path = path_no_ext+'.rst'
        self.html_path = path_no_ext+'.html'
        self.name, junk = os.path.splitext(self.pyp_name)
        self.rst_name = self.name+'.rst'
        self.html_name = self.name+'.html'


    def save(self, pathout=None):
        if pathout is None:
            pathout = self.rst_path
        pytexutils.writefile(pathout, self.rst_list)
        return pathout


img_pat = '(?:fig|image){(.*?)}'

class image(list_regexp_replacer):
    def __init__(self, pat=img_pat, **kwargs):
        list_regexp_replacer.__init__(self, pat=pat, **kwargs)
        self.decorator = image_decorator()


class centered_image(image):
    def __init__(self, pat=img_pat, **kwargs):
        image.__init__(self, pat=pat, **kwargs)
        self.center_dec = center_decorator()


    def replace_line(self, linein):
        q = self.p.search(linein)
        if q:
            img_path = q.group(1)
            image_list =  self.decorator(img_path)
            listout = self.center_dec(image_list)
            return listout
        else:
            return linein


class centered_figure_replacer(centered_image):
    def __init__(self, pat=img_pat, **kwargs):
        self.pat = pat
        self.p = re.compile(self.pat)
        self.decorator = centered_figure()


    def replace_line(self, linein):
        q = self.p.search(linein)
        if q:
            chunk = q.group(1)
            args_list = break_at_pipes(chunk)
            img_path = args_list.pop()
            my_opts, loners = OptionsDictFromList(args_list)
            assert len(loners) < 2, "Got more than one unlabeled option" + \
                   chunk
            if len(loners) == 1:
                my_opts['caption'] = loners[0]
            kwargs = {}
            if my_opts.has_key('caption'):
                kwargs['caption'] = my_opts['caption']
            listout =  self.decorator(img_path, **kwargs)
            return listout
        else:
            return linein



class link_decorator(rst_decorator):
    def __call__(self, match):
        link_text = match.group(1)
        target = match.group(2)
        lineout = '`%s <%s>`_' % (link_text, target)
        return lineout


class link_decorator2(rst_decorator):
    def __call__(self, target, text=None):
        if text is None:
            text = target
        lineout = '`%s <%s>`_' % (text, target)
        return lineout


class link_replacer(list_regexp_replacer):
    def __init__(self, pat='link{(.*?)\|(.*?)}', **kwargs):
        list_regexp_replacer.__init__(self, pat=pat, **kwargs)
        self.decorator = link_decorator()


    def replace_line(self, linein):
        q = self.p.search(linein)
        if q:
            lineout = self.p.sub(self.decorator, linein)
            return lineout
        else:
            return linein


class link_without_text_dec(link_decorator):
    def __call__(self, match):
        target = match.group(1)
        lineout = '`%s <%s>`_' % (target, target)
        return lineout


class link_replacer_without_text(link_replacer):
    def __init__(self, pat='link{(.*?)}', **kwargs):
        list_regexp_replacer.__init__(self, pat=pat, **kwargs)
        self.decorator = link_without_text_dec()


class blue_decorator(link_decorator):
    def __call__(self, match):
        lineout = ':blue:`%s`' % match.group(1)
        return lineout


class path_replacer(link_replacer):
    def __init__(self, pat='path{(.*?)}', **kwargs):
        list_regexp_replacer.__init__(self, pat=pat, **kwargs)
        self.decorator = blue_decorator()


class lstinline_replacer(link_replacer):
    def __init__(self, pat=r'\\lstinline!(.*?)!', **kwargs):
        list_regexp_replacer.__init__(self, pat=pat, **kwargs)
        self.decorator = blue_decorator()


rst_s5_header = r""".. -*- mode: rst -*-
.. include:: <s5defs.txt>

.. Configuration, see http://www.netzgesta.de/S5/references.php
.. meta::
   :tranSitions: false
   :fadeDuration: 100

.. |space| unicode:: 0x0020

"""

class Beamer_to_rst_paper(pyp_to_rst):
    def __init__(self, pyppath):
        pyp_to_rst.__init__(self, pyppath)
        self.converters = [section_to_level_1(), \
                           one_asterisk_to_level_2(), \
                           two_asterisks_to_list_level_1(), \
                           three_asterisks_to_list_level_2(), \
                           centered_image()]

    def fix_nested_lists(self):
        """rst really prefers that a new nest level be preceded by a
        blank line, so this method will find all level 3 bullets that
        are preceded by something other than a level 3 bullet and
        insert a blank line before it."""
        levels_to_fix = [2,3,4]
        for level in levels_to_fix:
            pat = '*' * level
            inds = self.rst_list.findall(pat)
            inds.reverse()
            first_inds = [item for item in inds if (item-1) not in inds]

            for ind in first_inds:
                self.rst_list.insert(ind, '')

    def convert(self):
        self.fix_nested_lists()
        for converter in self.converters:
            self.rst_list = converter.replace_list(self.rst_list)
        return self.rst_list


class pyp_doc_to_rst_paper(Beamer_to_rst_paper):
    def __init__(self, pyppath):
        pyp_to_rst.__init__(self, pyppath)
        self.converters = [section_to_section(), \
                           subsection_to_subsection(), \
                           subsubsection_to_subsubsection(), \
                           one_asterisks_to_list_level_1(), \
                           two_asterisks_to_list_level_2(), \
                           three_asterisks_to_list_level_3(), \
                           centered_figure_replacer(), \
                           figure_ref(), \
                           lstinline(), \
                           inlineeq()]



class Beamer_to_s5_pres(Beamer_to_rst_paper):
    def __init__(self, pyppath, title=None):
        Beamer_to_rst_paper.__init__(self, pyppath)
        self.converters = [#section_to_level_1(), \#don't know if this one makes sense, should probably just drop sections
                           one_asterisk_to_level_2(), \
                           two_asterisks_to_list_level_1(), \
                           three_asterisks_to_list_level_2(), \
                           four_asterisks_to_list_level_3(), \
                           centered_image(), \
                           link_replacer(), \
                           link_replacer_without_text(), \
                           path_replacer(), \
                           lstinline_replacer()]

        self.title = title


    def cmd(self):
        return 'python myrst2s5.py --theme-url="ui/advanced_utf" %s %s' % \
               (self.rst_path, self.html_path)


    def convert(self):
        Beamer_to_rst_paper.convert(self)
        self.rst_list.insert(0,rst_s5_header)
        if self.title:
            title_dec = rst_section_level_1()
            title_list = title_dec(self.title)
            self.rst_list[1:1] = title_list
        if self.rst_list[-1] != '':
            self.rst_list.append('')
        return self.rst_list


    def copy_stuff(self):
        pythonutil_path = rwkos.FindFullPath('pythonutil')
        filelist = ['pygments.css','myrst2s5.py']
        for curfile in filelist:
            src_path = os.path.join(pythonutil_path, curfile)
            dest_path = os.path.join(self.main_dir, curfile)
            shutil.copy2(src_path, dest_path)

        ui_path = os.path.join(pythonutil_path, 'ui')
        ui_dest = os.path.join(self.main_dir, 'ui')
        if not os.path.exists(ui_dest):
            shutil.copytree(ui_path, ui_dest)


    def rst_to_s5(self):
        cmd = 'python myrst2s5.py --theme-url="ui/ryan_s5" %s %s' \
              % (self.rst_name, self.html_name)
        print cmd
        curdir = os.getcwd()
        os.chdir(self.main_dir)
        os.system(cmd)
        os.chdir(curdir)


# How should this work?
#
# basicaly, I am tryping to map using regexps from my pyp to valid rst
#
# section headings need to be
#
#  =========
#  heading
#  =========
#
# and subsections I think need to be
#
#  subheading
#  ===========
#
#  and so on
#
#  The trick is knowing what the section headings are and what the
#  subsections are based on my various uses of pyp (i.e. Beamer
#  vs. documents vs. whatever) and knowing what the rst output will be
#  for (i.e. presentation using s5 or a document using rst2latex or
#  rst2html.
#
#  So, I need to regexp search and replace (I think), but with so
#  tricks to handle the fact that I might be replacing one line with 3
#  and the rst decorations need to be at least as long as the title
#  line.  And there need to be different mappings from pyp to rst for
#  different purposes.
#
#  I also then need to take things that are supposed to be bullet
#  points in Beamer and reduce the number of asterisks and add extra
#  white space (possibly) to make Beamer -> s5 work correctly with
#  nested lists.
#
#  So, I need something that taks a pyp line and returns the
#  appropriate rst line or lines after applying a list of rules.

if __name__ == '__main__':

    from optparse import OptionParser

    usage = 'usage: %prog [options] inputfile.pyp'
    parser = OptionParser(usage)


    parser.add_option("-r", "--runlatex", dest="runlatex", \
                      help="Run LaTeX after presentation is converted to tex.", \
                      default=1, type="int")

    parser.add_option("-s", "--sectiond", dest="sections", \
                      help="Indices of the sections of the document that you want converted to LaTeX.", \
                      default='', type="string")

    parser.add_option("-o", "--output", dest="output", \
                      help="Desired output path or filename.", \
                      default='', type="string")


    (options, args) = parser.parse_args()

    print('options='+str(options))
    print('args='+str(args))

    secstr = options.sections
    pathout = options.output

    import rwkos
    #mydir = rwkos.FindFullPath('siue/Research/papers/SciPy2008')
    #myfile = 'presentation_SciPy_2008_v2.pyp'
    #mypath = os.path.join(mydir, myfile)
    #mypyp = Beamer_to_rst_paper(mypath)

    #mydir = rwkos.FindFullPath('siue/classes/mechatronics/2008/python_intro')
    #myfile = 'python_intro.pyp'
    #mydir = rwkos.FindFullPath('siue/classes/mechatronics/2009/lectures/10_28_09/')
    #myfile = 'intro_to_PSoC.pyp'
    #mypath = os.path.join(mydir, myfile)
    mypath = args[0]
    mypyp = pyp_doc_to_rst_paper(mypath)
    #mypyp = Beamer_to_s5_pres(mypath)
    #mypyp = Beamer_to_s5_pres(mypath, title='Introduction to Mechatronics')
    mypyp.convert()
    mypyp.save()
    #mypyp.copy_stuff()
    #mypyp.rst_to_s5()
