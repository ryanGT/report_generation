import os
import txt_mixin, rwkos

class rst_decorator:
    def __init__(self, stringin=''):
        self.string = stringin


    def __call__(self, stringin):
        listout = [stringin]
        return listout


class image_decorator(rst_decorator):
    def __init__(self, stringin='', width=800):
        self.stringin = stringin
        self.width = width


    def __call__(self, pathin, width=None):
        if width is None:
            width = self.width
        line1 = '.. image:: %s' % pathin
        line2 = '   :width: %s' % width
        listout = [line1, line2, '']
        return listout


class figure_decorator(image_decorator):
    def __call__(self, pathin, caption=None, width='4.0in', \
                 target=None, height=None):
        if width is None and height is None:
            width = self.width
        line1 = '.. figure:: %s' % pathin
        listout = [line1]
        if width > 0:
            line2 = '   :width: %s' % width
            listout.append(line2)
        if height > 0:
            lineh = '   :height: %s' % height
            listout.append(lineh)
        if target:
            line3 = '   :target: %s' % target
            listout.append(line3)
        listout.append('')
        if caption:
            capline = '   '+caption
            listout.append(capline)
            listout.append('')
        return listout


class center_decorator(rst_decorator):
    def __init__(self, stringin='', ws=' '*4):
        self.stringin = stringin
        self.ws = ws

        
    def __call__(self, listin, ws=' '*4):
        if type(listin) == str:
            listin = [listin]
        line1 = '.. container:: center'
        listout = [ws+item for item in listin]
        listout.insert(0, '')
        listout.insert(1, line1)
        listout.insert(2, '')
        return listout


class centered_figure(rst_decorator):
    def __init__(self, *args, **kwargs):
        self.center_dec = center_decorator()
        self.fig_dec = figure_decorator()

            
    def __call__(self, *args, **kwargs):
        figlist = self.fig_dec(*args, **kwargs)
        listout = self.center_dec(figlist)
        return listout


    
class rst_section_level_1(rst_decorator):
    def __call__(self, stringin):
        dec_line = '='*(len(stringin)+1)
        listout = [dec_line, stringin, dec_line, '']
        return listout


class rst_section_level_2(rst_decorator):
    def __call__(self, stringin):
        dec_line = '='*(len(stringin)+1)
        listout = [stringin, dec_line, '']
        return listout


class rst_section_level_3(rst_decorator):
    def __call__(self, stringin):
        dec_line = '-'*(len(stringin)+1)
        listout = [stringin, dec_line, '']
        return listout


class rst_title_dec(rst_decorator):
    def __call__(self, stringin):
        dec_line = '='*(len(stringin)+1)
        listout = [dec_line, stringin, dec_line, '']
        return listout

class rst_subtitle_dec(rst_decorator):
    def __call__(self, stringin):
        dec_line = '~'*(len(stringin)+1)
        listout = [stringin, dec_line, '']
        return listout

class rst_section_dec:
    def __init__(self, symbol='='):
        self.symbol = symbol

    def __call__(self, stringin):
        dec_line = self.symbol*(len(stringin)+1)
        listout = [stringin, dec_line, '']
        return listout

class rst_subsection_dec(rst_section_dec):
    def __init__(self, symbol='-'):
        self.symbol = symbol


class rst_subsubsection_dec(rst_section_dec):
    def __init__(self, symbol='+'):
        self.symbol = symbol



class rst_file(txt_mixin.txt_file_with_list):
    """This class exists to programmatically create rst files in order
    to create reports and such."""
    def __init__(self, pathin=None, append=False):
        if append:
            txt_mixin.txt_file_with_list.__init__(self, pathin=pathin)
        else:
            #temporarily override pathin so that the file is not read
            txt_mixin.txt_file_with_list.__init__(self, pathin=None)
            self.pathin = pathin#then set pathin after
                                #txt_file_with_list.__init__
        self.title_dec = rst_section_level_1()
        self.subtitle_dec = rst_subtitle_dec()
        self.section_dec = rst_section_level_2()
        self.subsection_dec = rst_section_level_3()
        self.figure_dec = figure_decorator()
        self.centered_figure_dec = centered_figure()
        self.image_dec = image_decorator()
        self.saved = False
        if pathin is not None:
            pne, ext = os.path.splitext(self.pathin)
            self.htmlpath = pne+'.html'
        #self.centered_image_dec = centered_image()


    def add_header(self):
        mylist = ['.. include:: /home/ryan/git/report_generation/header.rst' , \
                  '']
        self.list.extend(mylist)


    def save(self):
        self.writefile(self.pathin)
        self.saved = True

        
    def add_title(self, title_text):
        title_list = self.title_dec(title_text)
        self.list.extend(title_list)


    def add_subtitle(self, subtitle_text):
        subtitle_list = self.subtitle_dec(subtitle_text)
        self.list.extend(subtitle_list)


    def add_enum_list(self, listin):
        enum_list = []

        for item in listin:
            curline = '#. ' + item
            enum_list.append(curline)

        enum_list.append('')
        
        self.list.extend(enum_list)

    def to_html(self):
        if not self.saved:
            self.save()
        if not rwkos.amiLinux():
            base_cmd = 'rst2html.py %s %s'
        else:
            base_cmd = 'rst2html %s %s'
        cmd = base_cmd % (self.pathin, self.htmlpath)
        print(cmd)
        os.system(cmd)


    def to_pdf(self):
        if not self.saved:
            self.save()
        if not rwkos.amiLinux():
            base_cmd = 'rst2html.py %s %s'
        else:
            base_cmd = 'rst2latex_rwk.py %s %s'
        cmd = base_cmd % (self.pathin, self.htmlpath)
        print(cmd)
        os.system(cmd)
        

    def add_figure(self, figpath, caption=None, width=None, \
                   height=None, **kwargs):
        fig_list = self.figure_dec(figpath, caption=caption, \
                                   width=width, height=height, \
                                   **kwargs)
        self.list.extend(fig_list)


    def add_body(self, body, padlines=True):
        if type(body) == str:
            body = [body]
        if padlines:
            self.list.append('')
        self.list.extend(body)
        if padlines:
            self.list.append('')


    def add_section(self, section_title):
        section_list = self.section_dec(section_title)
        self.list.extend(section_list)


    def add_subsection(self, subsection_title):
        subsection_list = self.subsection_dec(subsection_title)
        self.list.extend(subsection_list)


class beamer_file(rst_file):
    def add_header(self):
        mylist = ['.. include:: /home/ryan/git/report_generation/beamer_header.rst' , \
                  '']
        self.list.extend(mylist)
        

    def add_slide_title(self, slide_title):
        rst_file.add_section(self, slide_title)
        

    def add_figure(self, figpath, caption=None, width='4.0in', \
                   height=None, ws=None, **kwargs):
        fig_list = self.figure_dec(figpath, caption=caption, \
                                   width=width, height=height, \
                                   **kwargs)
        if ws is not None:
            out_list = [ws+item for item in fig_list]
        else:
            out_list = fig_list
        self.list.extend(out_list)
        

def add_up_link_to_rst(pathin, uplink_path=None):
    if uplink_path is None:
        uplink_path = '../index.html'
    myfile = txt_mixin.txt_file_with_list(pathin)
    inds = myfile.findallre('`up <.*index.html>`_')
    #print('inds = '+str(inds))
    if len(inds) > 1:
        print('more than one up match: '+pathin)
        for ind in inds:
            print('  ' + myfile.list[ind])
    if not inds:
        myfile.list.append('')
        myfile.list.append('`up <%s>`_' % uplink_path)
        myfile.save(pathin)


def _add_if_needed(pathin, pat, list_to_insert, ind=0):
    myfile = txt_mixin.txt_file_with_list(pathin)
    inds = myfile.findallre(pat)
    #print('inds = '+str(inds))
    if len(inds) > 1:
        print('more than one up match: '+pathin)
        for ind in inds:
            print('  ' + myfile.list[ind])
    if not inds:
        if (ind is None) or (ind == -1):
            myfile.list.extend(list_to_insert)
        else:
            myfile.list[ind:ind] = list_to_insert
        myfile.save(pathin)
    

def add_header(pathin):
    pat = r'\.\. include:: .*header\.rst'
    mylist = ['.. include:: /home/ryan/git/report_generation/header.rst' , \
              '']
    _add_if_needed(pathin, pat, mylist)


def add_beamer_header(pathin):
    pat = r'\.\. include:: .*beamer_header\.rst'
    mylist = ['.. include:: /home/ryan/git/report_generation/beamer_header.rst' , \
              '']
    _add_if_needed(pathin, pat, mylist)

                                         
def rst2html_fullpath(pathin, add_up_link=False, \
                      uplink_path=None):
    if add_up_link:
        add_up_link_to_rst(pathin, uplink_path=uplink_path)
    pne, ext = os.path.splitext(pathin)
    htmlpath = pne + '.html'
    if not rwkos.amiLinux():
        base_cmd = 'rst2html.py %s %s'
    else:
        base_cmd = 'rst2html %s %s'
    cmd = base_cmd % (pathin, htmlpath)
    os.system(cmd)
