"""This module contains one function, run_rst_sage which is intended
to be run from within sage.  It should allow an rst document
containing sage related symbolic stuff to be converted to tex, with an
option for running latex to gneerate the pdf.  This function is
intended to be the equivalent of calling rst2latex_rwk.py with the
--sage option.  This file has been created because the --sage option
causes sage to be loaded into memory each time, which is slow."""

# ==================
# ``run_example.py``
# ==================
#
# A script to convert example.rst into latex.
#
# This script shows how to use Docutils and Sphinx.
#
# Change ``TOOL`` to either ``docutils`` or ``sphinx`` 
# to choose which to use for the conversion.
#
# ::

import os

from docutils.core import publish_file
import py_directive#<- import py_directive and thats it


def run_rst_sage(filename, run_latex=1):
    rst_fn = filename
    fno, ext = os.path.splitext(rst_fn)
    EXAMPLE_FILE = rst_fn
    TOOL = 'docutils'
    tex_name = fno + '.tex'

    import latex_find_replace
    reload(latex_find_replace)
    py_directive.config['latex_find_replace_func'] = latex_find_replace._replace_latex

    overrides = {'stylesheet':'/Users/rkrauss/git/report_generation/rst_header.tex', \
                 'documentoptions':'12pt,letterpaper'}

    publish_file(source_path=EXAMPLE_FILE,\
                 destination_path=tex_name,\
                 writer_name='latex', \
                 settings_overrides=overrides, \
                 )


    if run_latex:
        cmd = 'pdflatex ' + tex_name
        os.system(cmd)
    
