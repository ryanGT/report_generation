import os, subprocess, txt_mixin

from portfolio_utils import seperator_sheet, many_sep_sheets

blank_path = '/Volumes/IOMEGA/siue/tenure/course_portfolios/blank_page.pdf'


def pdf_path(pathin):
    fno, ext = os.path.splitext(pathin)
    pdfout = fno + '.pdf'
    return pdfout


def get_pdf_pages(pathin):
    cmd = 'pdftk %s dump_data' % pathin
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE,stderr=subprocess.PIPE, shell=True)
    output, errors = p.communicate()

    mylist = output.split('\n')
    mylist2 = txt_mixin.txt_list(mylist)
    inds = mylist2.findall('NumberOfPages:')
    assert len(inds) == 1, 'Did not find exactly one match of "NumberOfPages:", inds = ' + str(inds)
    ind = inds[0]
    junk, page_str = mylist2[ind].split(':',1)
    page_str = page_str.strip()
    pages = int(page_str)
    return pages
    

class pdfcompiler(object):
    def __init__(self, basepath, outpath, main_sep_line, \
                 twosided=True):
        self.basepath = basepath
        self.outpath = outpath
        self.main_sep_line = main_sep_line
        self.twosided = twosided
        self.pdflist = []
        

    def _exec_cmd(self, cmd):
        curdir = os.getcwd()
        os.chdir(self.basepath)
        print(cmd)
        os.system(cmd)
        os.chdir(curdir)


    def append_blank(self):
        self.pdflist.append(blank_path)
        

    def append_single_page_pdf(self, pdfpathin, addblank=None):
        if addblank is None:
            addblank = self.twosided

        self.pdflist.append(pdfpathin)
        if addblank:
            self.append_blank()
            
        
    def append_single_page_rst(self, rst_path, addblank=None):
        rst_cmd = 'rst2latex_rwk.py %s' % rst_path
        self._exec_cmd(rst_cmd)

        rst_pdf_path = pdf_path(rst_path)

        self.append_single_page_pdf(rst_pdf_path, addblank=addblank)
        

    def append_contents(self, contents_path, addblank=None):
        self.append_single_page_rst(contents_path, addblank)


    def append_sep_sheet(self, pathin, line2, line3='', \
                         space2='1.5in', \
                         addblank=None):
        pne, ext = os.path.splitext(pathin)
        if not ext:
            pathin += '.tex'
        seperator_sheet(pathin, self.main_sep_line, \
                        line2=line2, line3=line3, \
                        space2=space2)
        sep_pdf = pdf_path(pathin)
        self.append_single_page_pdf(sep_pdf, addblank=addblank)


    def append_pdf(self, pathin):
        self.pdflist.append(pathin)
        if self.twosided:
            pages = get_pdf_pages(pathin)
            if (pages % 2) != 0:
                self.append_blank()
                

    def compile_final_pdf(self):
        filestr = ' '.join(self.pdflist)
        cmd = 'pdftk_merge.py ' + filestr + ' ' + self.outpath
        self._exec_cmd(cmd)
        


import pyPdf

def get_num_pages(pathin):
    doc = pyPdf.PdfFileReader(file(pathin,'rb'))
    N = doc.getNumPages()
    return N


class pdf_file(object):
    """As part of my TEA dossier creation, I want to autogenerate
    bookmarks and the table of contents for my dossier.  This will
    include keeping track of the start page for each pdf and having
    options for whether or not to include the pdf in the table of
    contents and bookmarks."""
    def __init__(self, filepath, \
                 start_page=-1,\
                 bookmark_name=None, \
                 bookmark_level=1, \
                 toc_name=None,
                 toc_level=None):
        self.filepath = filepath
        #self.pages = get_pdf_pages(filepath)
        self.start_page = start_page
        self.pages = get_num_pages(filepath)
        self.bookmark_name = bookmark_name
        self.bookmark_level = bookmark_level
        if toc_name is None:
            toc_name = bookmark_name
        if toc_level is None:
            toc_level = bookmark_level
        self.toc_name = toc_name
        self.toc_level = toc_level


    def generate_bookmark_lines(self):
        if self.bookmark_name is None:
            return None
        else:
            line1 = 'BookmarkBegin'
            line2 = 'BookmarkTitle: %s' % self.bookmark_name
            line3 = 'BookmarkLevel: %i' % self.bookmark_level
            line4 = 'BookmarkPageNumber: %i' % self.start_page
            return [line1, line2, line3, line4]


    def gen_toc_line(self):
        #Section 2: Implementation & 10 \rule{0pt}{1.2EM}\\
        #\hspace{0.25in} Section 2. A: More Stuff & 15 \rule{0pt}{1.2EM}\\

        #\hyperlink{page.2}{Go to page 2}
        if self.toc_name is None:
            return None
        
        toc_str = ''

        if self.toc_level == 2:
            toc_str += '\\hspace{0.25in} '
        elif self.toc_level == 3:
            toc_str += '\\hspace{0.5in} '

        #href_part = '\\hyperlink{page.%i}{%i}' % (self.start_page, self.start_page)
        href_part = '%i' % self.start_page
        toc_str += self.toc_name + ' & ' + href_part + ' \\rule{0pt}{1.2EM} \\\\'
        
        return toc_str
            


    def gen_pages_line(self):
        """generate the latex code for adding self to a pdfpages document"""
        fno, ext = os.path.splitext(self.filepath)
        if self.bookmark_name is None:
            lineout = '\\includepdf[pages=-,]{%s}' % self.filepath
        else:
            if self.bookmark_level == 1:
                toc_part = '{1,section,1,%s,pdf:%s}' % (self.bookmark_name, \
                                                        fno)
            elif self.bookmark_level == 2:
                toc_part = '{1,subsection,2,%s,pdf:%s}' % (self.bookmark_name, \
                                                           fno)
            elif self.bookmark_level == 3:
                toc_part = '{1,subsubsection,3,%s,pdf:%s}' % (self.bookmark_name, \
                                                              fno)
            lineout = '\\includepdf[pages=-,addtotoc=%s]{%s}' % (toc_part, self.filepath)

        return lineout


class pdf_document(object):
    """This will be the base class for the new pdf document that is
    compiled from a list of pdf documents and includes autogenerated
    toc and bookmarks."""
    def __init__(self, outpath, toc_ind=1):
        self.outpath = outpath
        self.start_page = 1
        self.pdf_list = []
        self.toc_ind = toc_ind


    def append_one_pdf(self, filepath, **kwargs):
        cur_file = pdf_file(filepath, start_page=self.start_page, \
                            **kwargs)
        self.pdf_list.append(cur_file)
        self.start_page += cur_file.pages


    def append_pdf_instance(self, pdf_inst):
        pdf_inst.start_page = self.start_page
        self.start_page += pdf_inst.pages
        self.pdf_list.append(pdf_inst)

    
    def generate_first_pdf(self):
        """generate the first pdf with no toc or bookmarks"""
        cmd = 'pdftk '
        for cur_pdf in self.pdf_list:
            cmd += cur_pdf.filepath + ' '

        fno, ext = os.path.splitext(self.outpath)
        nb_path = fno + '_no_bookmarks.pdf'
        cmd += 'cat output ' + nb_path
        self.nb_path = nb_path
        print(cmd)
        os.system(cmd)


    def dump_data(self):
        """dump the data from the first pdf so that we can append the
        bookmarks to it"""
        fno, ext = os.path.splitext(self.outpath)
        data_path = fno + '_no_bookmarks_info.info'
        cmd = 'pdftk %s dump_data output %s' % (self.nb_path, data_path)
        self.data_path = data_path
        os.system(cmd)


    def append_bookmarks_to_info(self):
        info_file = txt_mixin.txt_file_with_list(self.data_path)
        in_list = info_file.list
        for cur_pdf in self.pdf_list:
            cur_bm = cur_pdf.generate_bookmark_lines()
            if cur_bm is not None:
                in_list.extend(cur_bm)

        fno, ext = os.path.splitext(self.outpath)
        info_path = fno + '.info'
        txt_mixin.dump(info_path, in_list)
        self.info_path = info_path


    def update_info(self):
        """use the pdftk update_info command to merge the new
        bookmarks file in"""
        cmd = 'pdftk %s update_info %s output %s' % (self.nb_path, self.info_path, self.outpath)
        print(cmd)
        os.system(cmd)
        

    def generate_toc(self):
        fno, ext = os.path.splitext(self.outpath)
        toc_path = fno + '_toc.tex'
        mylist = ['\\input{toc_header}',\
                  '\\begin{document}',\
                  '\\begin{center}',\
                  '\\begin{tabularx}{0.95\\textwidth}{Xr}',\
                  '{\\large \\textbf{Table of Contents}} & page \\\\',\
                  ]

        out = mylist.append
        
        first = 1
        for cur_pdf in self.pdf_list:
            curline = cur_pdf.gen_toc_line()
            if curline is not None:
                if first:
                    first = 0
                else:
                    out('\\hline')
            
                out(curline)

        out('\\end{tabularx}')
        out('\\end{center}')
        out('\\end{document}')

        txt_mixin.dump(toc_path, mylist)

        cmd = 'pdflatex ' + toc_path
        os.system(cmd)
        
        old_toc = self.pdf_list[self.toc_ind]

        toc_fno, ext = os.path.splitext(toc_path)
        toc_pdf_path = toc_fno + '.pdf'
        old_toc.filepath = toc_pdf_path


    def gen_pdf_pages(self):
        lines = []
        for cur_pdf in self.pdf_list:
            curline = cur_pdf.gen_pages_line()
            lines.append(curline)

        fno, ext = os.path.splitext(self.outpath)
        pages_path = fno + '_pdfpages.tex'
        txt_mixin.dump(pages_path, lines)
