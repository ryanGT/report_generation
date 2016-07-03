#!/usr/bin/python
import os, glob, time, shutil
from optparse import OptionParser
from replacelist import ReplaceList,AppendFRPatterns
from pytex import PythonFile
import py2pyp

import pyp_to_rst, rwkos

import sys


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

parser.add_option("-n", "--nohead", dest="nohead", \
                  help="Save with no header.", \
                  default=0, type="int")

parser.add_option("-c", "--clean", dest="clean_output", \
                  help="Remove all the files created from this script and LaTeX.", \
                  default=1, type="int")

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
pathto,basename = os.path.split(pne)
if pne[-4:] == '_raw':
    raw = 1
    clean_path = pne[0:-4]+'.py'

if not pathout:
    if raw:
        pathout = pne[0:-4]+'.pyp'
    else:
        pathout = None

frpatterns_path = os.path.join(os.path.splitext(py_path)[0],'frpatterns.txt')
replacelist = ReplaceList()#frpath=frpatterns_path)
replacelist.ReadFRFile()

mypy = py2pyp.python_file(py_path, outputpath=pathout)
mypy.Execute()
mypy.To_PYP(usetex=True, echo=echo, full_echo=echo,replacelist=replacelist)

if raw:
    mypy.clean_comments()
    mypy.writefile(clean_path, listin=mypy.clean_lines)

if title:
    mypy.pyp_list.insert(0, '\\textbf{\\Large %s}' % title)

append_show = 0
if append_show:
    mypy.pyp_list.append('code{show()}')

pyp_path = mypy.save()

if options.nohead:
    cmd = 'document_gen.py -n 1 -c %s %s' % (options.clean_output,pyp_path)
else:
    cmd = 'document_gen.py -c %s %s' % (options.clean_output,pyp_path)

os.system(cmd)

#append any new potential replacements
#findlist=[]
#findlist.extend(tp.FindLHSs())
#replacelist.AppendFRFile(findlist)
if options.clean_output:
    os.unlink(pyp_path)

#append any new potential replacements
findlist=[]
findlist.extend(mypy.FindLHSs())
AppendFRPatterns(findlist)
