#!/usr/bin/env python
import os, glob, time, shutil
from optparse import OptionParser
from pytexutils import cleanLatexOutputFiles

import pyp_converter, rwkos

import sys


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

parser.add_option("-c", "--clean", dest="clean_output", \
                  help="Remove all the files created from this script and LaTeX.", \
                  default=1, type="int")
                  
(options, args) = parser.parse_args()

print('options='+str(options))
print('args='+str(args))

secstr = options.sections
pathout = options.output

if secstr:
    exec('seclist=['+secstr+']')
else:
    seclist = None

if not pathout:
    pathout = None
    
pyp_path = rwkos.FindFullPath(args[0])
print('pyp_path='+pyp_path)
my_doc = pyp_converter.Latex_document(pyp_path, pathout=pathout)
my_doc.to_latex(sections=seclist)
my_doc.save()

if options.runlatex:
    my_doc.run_latex()

pathto,pyp_file = os.path.split(pyp_path)
basename,ext = os.path.splitext(pyp_file)
if options.runlatex and options.clean_output:
    cleanLatexOutputFiles(pathto,basename,exts=['log','aux','out'])
