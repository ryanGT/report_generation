import os, glob, relpath, shutil
import txt_mixin

def one_lecture_nh(lecture_path, glob_pat, relfolder='screensize', \
                   main_path=None, spp=8):
    """spp means slides per page"""
    if main_path is None:
        main_path = lecture_path
    slide_folder = os.path.join(lecture_path, relfolder)
    full_glob_pat = os.path.join(slide_folder, glob_pat)
    slide_paths = glob.glob(full_glob_pat)
    slide_paths.sort()

    outlist = []
    out = outlist.append

    N = len(slide_paths)
    num_on_page = 0

    for i, curslide in enumerate(slide_paths):
        if (i % spp) == 0:
            num_on_page = 0
            out('\\begin{tabular}{|c|c|}')
            out('\\hline')
        currel = relpath.relpath(curslide, base=main_path)
        curent = '\\includegraphics[width=0.475\\textwidth]{%s}' % currel
        num_on_page += 1
        out(curent)
        if i < (N-1):
            if (i % 2) == 0:
                out('&')
            elif (i % 2) == 1:
                out('\\\\')
                out('\\hline')

            if ((i+1) % spp) == 0:
                out('\\end{tabular}')

    if (i % 2) == 0 and (num_on_page > 1):
        out('&')

    out('\\\\')
    out('\\hline')

    out('\\end{tabular}')

    return outlist


def gimp_lectures_one_course(lecture_path, date_list, \
                             outname, glob_pat, \
                             lhead, rhead, spp=8):
    header_path = '/home/ryan/siue/tenure/course_portfolios/gimp_lecture_header.tex'
    outlist = ['\\input{%s}' % header_path]
    out = outlist.append
    out('\\pagestyle{fancy}')
    ws = ' '*4
    out(ws + '\\lhead{%s}' % lhead)
    out(ws + '\\rhead{%s}' % rhead)
    out('\\begin{document}')

    N = len(date_list)

    for i, date_str in enumerate(date_list):
        curpath = os.path.join(lecture_path, date_str)
        curlist = one_lecture_nh(curpath, glob_pat, main_path=lecture_path, spp=spp)
        outlist.extend(curlist)
        if i < (N - 1):
            out('')
            out('\\pagebreak')
            out('')

    out('\\end{document}')

    outpath = os.path.join(lecture_path, outname)
    txt_mixin.dump(outpath, outlist)
    return outpath


def run_latex_and_copy(texpath, portfolio_dir):
    texfolder, filename = os.path.split(texpath)
    pne, ext = os.path.splitext(texpath)
    pdfpath = pne + '.pdf'
    src_folder, pdfname = os.path.split(pdfpath)
    dest_path = os.path.join(portfolio_dir, pdfname)
    curdir = os.getcwd()
    try:
        cmd = 'pdflatex %s' % filename
        os.chdir(texfolder)
        os.system(cmd)
        shutil.copy(pdfpath, dest_path)
    finally:
        os.chdir(curdir)



if __name__ == '__main__':
from IPython.core.debugger import Pdb

    lecture_path_592 = '/home/ryan/nonlinear_controls_2011/lectures'
    date_list_592 = ['01_18_11', \
                     '02_03_11', \
                     '02_08_11', \
                     '02_10_11', \
                     '04_05_11']
    outname_592 = 'gimp_lectures_592.tex'
    lhead_592 = 'ME 592: Nonlinear Controls'
    rhead_592 = 'Spring 2011'
    glob_pat_592 = 'ME592_*.jpg'#screensize images are jpg
    outpath = gimp_lectures_one_course(lecture_path_592, date_list_592, \
                                       outname=outname_592, \
                                       glob_pat=glob_pat_592, \
                                       lhead=lhead_592, \
                                       rhead=rhead_592)
    portfolio_dir_592 = '/home/ryan/siue/tenure/course_portfolios/592_nonlinear_controls'
    run_latex_and_copy(outpath, portfolio_dir_592)

