import os, subprocess, txt_mixin

from portfolio_utils import seperator_sheet, many_sep_sheets

blank_path = '/home/ryan/siue/tenure/course_portfolios/blank_page.pdf'


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
        

