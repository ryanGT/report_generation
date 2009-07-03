#!/usr/bin/env python
import os, subprocess

import pdb

header = r"""\documentclass[12pt]{article}
\newcommand{\be}{\begin{equation}}
\newcommand{\ee}{\end{equation}}
\newcommand{\M}[1]{\left[\mathbf{#1}\right]}
\usepackage{fancyhdr}
\usepackage{amsmath}
\renewcommand{\v}[1]{\left\{\mathbf{#1}\right\}}
\begin{document}
\thispagestyle{empty}
"""

def wrap_eq_in_full_tex(eq_in):
    eq_line = '$$ %s $$\n' % eq_in
    tex_code = header + eq_line + '\\end{document}'
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

def eqn_to_file_in_cache(eq_in, cache_dir=None, filename='temp_out.tex'):
    tex_code = wrap_eq_in_full_tex(eq_in)
    cache_dir = find_cache_dir(cache_dir)
    filepath = os.path.join(cache_dir, filename)
    tex_code_to_file(tex_code, filepath)

def read_eqn_from_file(filename='temp.tex', cache_dir=None):
    cache_dir = find_cache_dir(cache_dir)
    filepath = os.path.join(cache_dir, filename)
    f = open(filepath, 'rb')
    text = f.readlines()
    clean_text = text.replace('\n',' ')
    clean_text = clean_text.strip()
    return clean_text
    
def run_latex_dvi_png(pathin):
    curdir = os.getcwd()
    tex_dir, file_name = os.path.split(pathin)
    fno, ext = os.path.splitext(file_name)
    dvi_name = fno+'.dvi'
    try:
        os.chdir(tex_dir)
        latexstr = 'latex -interaction=nonstopmode '+ file_name
        p = subprocess.Popen(latexstr, shell=True, \
                             stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        output, errors = p.communicate()
        print(output)
        dvipng_cmd = "dvipng -D 600 -bg 'Transparent' -T tight "+dvi_name
        p2 = subprocess.Popen(dvipng_cmd, shell=True, \
                              stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        output2, errors2 = p2.communicate()
    finally:
        os.chdir(curdir)
    return dvi_name

def log_eq(eq_in, log_name=None, cache_dir=None):
    
    
def eq_to_dvi_png(eq_in, file_name='temp.tex', cache_dir=None, \
                  log=True):
    pass

def read_from_file_dvi_png(file_name='temp.tex', cache_dir=None, \
                           log=True):
    pass
