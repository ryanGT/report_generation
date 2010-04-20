#!/usr/bin/env python
import os, subprocess

import pdb

import rwkmisc

header = r"""\documentclass[12pt, fleqn]{article}
\newcommand{\be}{\begin{equation}}
\newcommand{\ee}{\end{equation}}
\newcommand{\M}[1]{\left[\mathbf{#1}\right]}
\usepackage{fancyhdr}
\usepackage{amsmath}
\renewcommand{\v}[1]{\left\{\mathbf{#1}\right\}}
\newcommand{\twobytwo}[4]{\begin{bmatrix} #1 & #2 \\ #3 & #4 \end{bmatrix}}
\newcommand{\twobyone}[2]{\begin{Bmatrix} #1 \\ #2\end{Bmatrix}}
\makeatletter
\setlength\@mathmargin{5pt}
\makeatother
\begin{document}
\thispagestyle{empty}
\flushleft
"""

def wrap_eq_in_dollar_signs(eq_in):
    eq_in = eq_in.strip()
    eq_line = '$$ %s $$' % eq_in
    return eq_line

def wrap_eq_in_eqn_star(eq_in):
    eq_in = eq_in.strip()
    eq_line = '\\begin{equation*}\n %s \n\\end{equation*}\n' % eq_in
    return eq_line

def wrap_latex_in_full_tex(text_in):
    if text_in[-1] != '\n':
        text_in += '\n'
    tex_code = header + text_in + '\\end{document}'
    return tex_code

def tex_code_to_file(code, filepath):
    f = open(filepath, 'wb')
    f.writelines(code)
    f.close()

def find_cache_dir(cache_dir=None):
    if cache_dir is None:
        home_dir = os.getenv('HOME') or os.getenv('USERPROFILE')
        cache_dir = os.path.join(home_dir, '.latex_dvi_png_cache')

    if not os.path.exists(cache_dir):
        os.mkdir(cache_dir)
    return cache_dir

def latex_to_file_in_cache(latex_in, cache_dir=None, \
                           filename='temp_out.tex'):
    tex_code = wrap_latex_in_full_tex(latex_in)
    cache_dir = find_cache_dir(cache_dir)
    filepath = os.path.join(cache_dir, filename)
    tex_code_to_file(tex_code, filepath)
    return filepath

def eqn_to_file_in_cache(eq_in, *args, **kwargs):
    eq_line = wrap_eq_in_eqn_star(eq_in)
    return latex_to_file_in_cache(eq_line, *args, **kwargs)

def read_eqn_from_file(filename='temp.tex', cache_dir=None):
    cache_dir = find_cache_dir(cache_dir)
    filepath = os.path.join(cache_dir, filename)
    f = open(filepath, 'rb')
    text = f.readlines()
    clean_text = ' '.join(text)
    clean_text = clean_text.replace('\n',' ')
    clean_text = clean_text.strip()
    return clean_text
    
def run_latex_dvi_png(pathin, res=750, bg_str=None):
    """bg_str = 'rgb 1.0 1.0 1.0' should be white.
    bg_str='Transparent' could also be used."""
    if bg_str is None:
        bg_str = "'rgb 1.0 1.0 1.0'"
    curdir = os.getcwd()
    tex_dir, filename = os.path.split(pathin)
    fno, ext = os.path.splitext(filename)
    dvi_name = fno+'.dvi'
    try:
        os.chdir(tex_dir)
        latexstr = 'latex -interaction=nonstopmode '+ filename
        p = subprocess.Popen(latexstr, shell=True, \
                             stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        output, errors = p.communicate()
        print(output)
        dvipng_cmd = "dvipng -D "+str(res)+" -bg " + bg_str + " -T tight "+dvi_name
        p2 = subprocess.Popen(dvipng_cmd, shell=True, \
                              stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        output2, errors2 = p2.communicate()
    finally:
        os.chdir(curdir)
    return dvi_name

def log_eq(eq_in, log_name=None, cache_dir=None):
    cache_dir = find_cache_dir(cache_dir)
    if log_name is None:
        log_name = 'tex_dvi_log_'+rwkmisc.get_date_str()+'.tex'
    log_path = os.path.join(cache_dir, log_name)
    f = open(log_path, 'ab')
    f.write(eq_in +'\n')
    f.close()

def find_png_name(dvi_name='temp_out.dvi', cache_dir=None):
    fno, ext = os.path.splitext(dvi_name)
    pngname = fno+'1.png'
    cache_dir = find_cache_dir(cache_dir)
    pngpath = os.path.join(cache_dir, pngname)
    if os.path.exists(pngpath):
        return pngpath
    
def latex_to_dvi_png(latex_in, filename='temp_out.tex', cache_dir=None, \
                     log=True, bg_str=None, res=750):
    if log:
        log_eq(latex_in, cache_dir=None)
    filepath = latex_to_file_in_cache(latex_in, filename=filename, \
                                      cache_dir=cache_dir)
    dvi_name = run_latex_dvi_png(filepath, bg_str=bg_str, res=res)
    return find_png_name(dvi_name, cache_dir=cache_dir)

def eq_to_dvi_png(eq_in, *args, **kwargs):
    latex_line = wrap_eq_in_eqn_star(eq_in)
    return latex_to_dvi_png(latex_line, *args, **kwargs)

def read_from_file_dvi_png(filename='temp.tex', cache_dir=None, \
                           log=True, **kwargs):
    eq_in = read_eqn_from_file(filename, cache_dir=cache_dir)
    fno, ext = os.path.splitext(filename)
    outname = fno+'_out.tex'
    return eq_to_dvi_png(eq_in, filename=outname, \
                         cache_dir=cache_dir, log=log, **kwargs)


if __name__ == '__main__':
    from optparse import OptionParser

    usage = 'usage: %prog [options] inputfile.txt'
    parser = OptionParser(usage)


    parser.add_option("-r", "--res", dest="res", \
                  help="Resolution in dpi for dvi to png.", \
                  default=600, type="int")

    (options, args) = parser.parse_args()
    pathin = args[0]
    folder, filename = os.path.split(pathin)
    if not folder:
        folder ='.'
    temppng = read_from_file_dvi_png(filename, cache_dir=folder, \
                                     res=options.res)
    pne, ext = os.path.splitext(pathin)
    pngpath = pne + '.png'

    import shutil
    shutil.move(temppng, pngpath)
    
