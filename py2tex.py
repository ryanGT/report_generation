#!/usr/bin/python
import os, glob, time, shutil
from optparse import OptionParser

import py2pyp

import pyp_to_rst, rwkos

import sys

#from IPython.Debugger import Pdb

usage = 'usage: %prog [options] inputfile.py'
parser = OptionParser(usage)

parser.add_option("-o", "--output", dest="output", \
                  help="Desired output path or filename.", \
                  default='', type="string")

parser.add_option("-t", "--title", dest="title", \
                  help="Title for the LaTeX document.", \
                  default='', type="string")

parser.add_option("-e", "--echo", dest="echo", \
                  help="Echo the python code. 0 = not at all, 1 = first, 2 = after", \
                  default=0, type="int")

                  
(options, args) = parser.parse_args()

print('options='+str(options))
print('args='+str(args))

pathout = options.output
title = options.title
echo = options.echo
curdir = os.getcwd()
print('curdir='+curdir)
if curdir not in sys.path:
    sys.path.append(curdir)
    
py_path = rwkos.FindFullPath(args[0])

raw = 0
pne, ext = os.path.splitext(py_path)
if pne[-4:] == '_raw':
    raw = 1
    clean_path = pne[0:-4]+'.py'

if not pathout:
    if raw:
        pathout = pne[0:-4]+'.pyp'
    else:
        pathout = None




mypy = py2pyp.python_file(py_path, outputpath=pathout)
mypy.Execute()
mypy.To_PYP(usetex=True, echo=echo, full_echo=echo)

if raw:
    mypy.clean_comments()
    mypy.writefile(clean_path, listin=mypy.clean_lines)
    
if title:
    mypy.pyp_list.insert(0, '\\textbf{\\Large %s}' % title)

append_show = 0
if append_show:
    mypy.pyp_list.append('code{show()}')
    
pyp_path = mypy.save()

cmd = 'document_gen.py %s' % pyp_path
print(cmd)
os.system(cmd)


## mypyp = pyp_to_rst.pyp_doc_to_rst_paper(pyp_path)
## mypyp.convert()
## rst_path = mypyp.save()

## pne, ext = os.path.splitext(rst_path)
## html_path = pne+'.tex'
## cmd = 'rst2html %s %s' % (rst_path, html_path)
## print(cmd)
## os.system(cmd)
