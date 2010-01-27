#!/usr/bin/python
from optparse import OptionParser

import texpy
reload(texpy)

import os,sys,replacelist

usage = 'usage: %prog [options] inputfile.tex'
parser = OptionParser(usage)


parser.add_option("-n", "--nohead", dest="nohead", \
                  help="Save with no head to be able to include in another LaTeX file.", \
                  default=0, type="int")

(options, args) = parser.parse_args()
print('options='+str(options))
print('args='+str(args))

#define the replacelist to make a pretty output
replacelist = replacelist.ReplaceList()
replacelist.ReadFRFile()

#define the file/filepath
inpath = args[0]#sys.argv[1]
fno, ext = os.path.splitext(inpath)
outpath = fno+'_out.tex'
fullpath = os.path.join(os.getcwd(),inpath)

#parse the file and execut the code
tp = texpy.TexPyFile(fullpath)
tp.Execute(star=True,replacelist=replacelist,echo=0)

#save the file and run latex
if options.nohead==1:
    tp.SaveLatex(outpath,ed=False)
else:
    tp.AddHeader()
    tp.SaveLatex(outpath)
    tp.RunLatex(dvi=False)

#append any new potential replacements
findlist=[]
findlist.extend(tp.FindLHSs())
replacelist.AppendFRFile(findlist)


